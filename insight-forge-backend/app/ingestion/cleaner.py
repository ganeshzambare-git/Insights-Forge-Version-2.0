"""
Insight Forge V2 — Lightweight Ingestion Cleaner.

Parses an uploaded CSV/JSON dataset and materializes clean rows into
``student_metrics`` (creating cohorts/student users as needed), then marks the
dataset Ready with a data-quality health score. Runs as a FastAPI background
task (no Celery). Uses only the Python standard library — no pandas/scikit.

Expected columns (header names are matched case-insensitively, with common
aliases):

    student_email      (aliases: email)
    cohort_code        (aliases: cohort, class, section)
    raw_average_grade  (aliases: grade, marks, score)   0-100
    attendance_percentage (aliases: attendance)         0-100
    reporting_period   (aliases: term, semester)        e.g. "Fall 2026"
"""

from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select, text

from app.core.enums import DatasetStatus, TaskStatus
from app.core.security import hash_password
from app.db.session import async_session_maker
from app.models.background_task import BackgroundTask
from app.models.cohort import Cohort
from app.models.dataset import Dataset
from app.models.student_metric import StudentMetric
from app.models.user import User

logger = logging.getLogger("app.ingestion.cleaner")

# Header alias → canonical field.
_ALIASES = {
    "student_email": "email", "email": "email", "e-mail": "email",
    "student email": "email",
    "cohort_code": "cohort", "cohort": "cohort", "class": "cohort",
    "section": "cohort", "cohort code": "cohort",
    "raw_average_grade": "grade", "grade": "grade", "marks": "grade",
    "score": "grade", "average_grade": "grade", "avg_grade": "grade",
    "attendance_percentage": "attendance", "attendance": "attendance",
    "attendance_pct": "attendance", "attendance %": "attendance",
    "reporting_period": "period", "term": "period", "semester": "period",
    "period": "period",
}

# Placeholder password for auto-created students (they log in via SSO/reset).
_IMPORT_PASSWORD = "ImportedStudent#2026"


def _risk_status(grade: float, attendance: float) -> str:
    if grade < 60 or attendance < 70:
        return "Critical"
    if grade < 75 or attendance < 85:
        return "Amber"
    return "Safe"


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, InvalidOperation):
        return None


def _canonical_row(row: dict) -> dict:
    """Map an arbitrary row's headers to canonical field names."""
    out: dict[str, str] = {}
    for key, val in row.items():
        if key is None:
            continue
        canon = _ALIASES.get(str(key).strip().lower())
        if canon and canon not in out:
            out[canon] = val
    return out


def _parse_records(raw: bytes, source_format: str) -> list[dict]:
    """Parse file bytes into a list of dict rows (CSV or JSON)."""
    text_data = raw.decode("utf-8-sig", errors="replace")
    if source_format == "json":
        data = json.loads(text_data)
        if isinstance(data, dict):
            data = data.get("records") or data.get("data") or [data]
        return [r for r in data if isinstance(r, dict)]
    # default: CSV
    reader = csv.DictReader(io.StringIO(text_data))
    return list(reader)


async def process_dataset(
    dataset_id: uuid.UUID, tenant_id: uuid.UUID, storage_uri: str
) -> None:
    """Clean an uploaded dataset into student_metrics and mark it Ready.

    Runs in its own tenant-scoped session (background task context).
    """
    now = datetime.now(timezone.utc)
    task_id = uuid.uuid4()
    try:
        async with async_session_maker() as session:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :t, true)"),
                {"t": str(tenant_id)},
            )

            dataset = await session.get(Dataset, dataset_id)
            if dataset is None:
                logger.warning("Dataset %s not found for cleaning", dataset_id)
                return

            # Register a Running background task for the monitor.
            session.add(
                BackgroundTask(
                    task_id=task_id,
                    tenant_id=tenant_id,
                    task_type="DATA_CLEANING",
                    status=TaskStatus.RUNNING.value,
                    progress_pct=10,
                    started_at=now,
                    timeline=[{"event": "Cleaning started", "timestamp": now.isoformat()}],
                )
            )
            dataset.processing_status = DatasetStatus.PROCESSING.value
            await session.flush()

            # Read + parse the stored file.
            with open(storage_uri, "rb") as fh:
                raw = fh.read()
            records = _parse_records(raw, (dataset.source_format or "csv").lower())

            inserted, skipped = await _materialize(
                session, tenant_id, records
            )
            total = inserted + skipped
            health = round((inserted / total) * 100, 2) if total else 0.0

            dataset.processing_status = DatasetStatus.READY.value
            dataset.row_count = inserted
            dataset.health_score = Decimal(str(health))

            done = datetime.now(timezone.utc)
            task = await session.get(BackgroundTask, task_id)
            if task is not None:
                task.status = TaskStatus.COMPLETED.value
                task.progress_pct = 100
                task.completed_at = done
                task.result = {
                    "rows_inserted": inserted,
                    "rows_skipped": skipped,
                    "health_score": health,
                }
                task.timeline = list(task.timeline) + [
                    {"event": f"Inserted {inserted} metrics", "timestamp": done.isoformat()}
                ]

            await session.commit()
        logger.info(
            "Cleaned dataset %s: %s inserted, %s skipped", dataset_id, inserted, skipped
        )
    except Exception as exc:  # mark dataset + task Failed, never crash the app
        logger.exception("Cleaning failed for dataset %s", dataset_id)
        await _mark_failed(dataset_id, tenant_id, task_id, str(exc))


async def _materialize(session, tenant_id: uuid.UUID, records: list[dict]) -> tuple[int, int]:
    """Insert clean rows into student_metrics; returns (inserted, skipped)."""
    pw_hash = hash_password(_IMPORT_PASSWORD)
    cohort_cache: dict[str, uuid.UUID] = {}
    user_cache: dict[str, uuid.UUID] = {}
    inserted = 0
    skipped = 0

    for raw_row in records:
        row = _canonical_row(raw_row)
        email = (row.get("email") or "").strip().lower()
        cohort_code = (row.get("cohort") or "").strip().upper()
        grade = _to_float(row.get("grade"))
        attendance = _to_float(row.get("attendance"))
        period = (row.get("period") or "Imported").strip() or "Imported"

        # Required, valid data only — everything else lowers the health score.
        if not email or not cohort_code or grade is None or attendance is None:
            skipped += 1
            continue
        grade = max(0.0, min(100.0, grade))
        attendance = max(0.0, min(100.0, attendance))

        cohort_id = await _get_or_create_cohort(
            session, tenant_id, cohort_code, cohort_cache
        )
        student_id = await _get_or_create_student(
            session, tenant_id, email, pw_hash, user_cache
        )

        session.add(
            StudentMetric(
                tenant_id=tenant_id,
                student_user_id=student_id,
                cohort_id=cohort_id,
                raw_average_grade=Decimal(str(round(grade, 2))),
                normalized_grade_score=Decimal(str(round(grade, 2))),
                attendance_percentage=Decimal(str(round(attendance, 2))),
                success_indicator_status=_risk_status(grade, attendance),
                reporting_period=period,
            )
        )
        inserted += 1

    return inserted, skipped


async def _get_or_create_cohort(
    session, tenant_id: uuid.UUID, code: str, cache: dict[str, uuid.UUID]
) -> uuid.UUID:
    if code in cache:
        return cache[code]
    existing = (
        await session.execute(
            select(Cohort.cohort_id).where(
                Cohort.tenant_id == tenant_id, Cohort.cohort_code == code
            )
        )
    ).scalar_one_or_none()
    if existing:
        cache[code] = existing
        return existing
    cohort = Cohort(
        cohort_id=uuid.uuid4(),
        tenant_id=tenant_id,
        cohort_code=code,
        department_scope=code.split("-")[0] if "-" in code else code,
    )
    session.add(cohort)
    await session.flush()
    cache[code] = cohort.cohort_id
    return cohort.cohort_id


async def _get_or_create_student(
    session, tenant_id: uuid.UUID, email: str, pw_hash: str, cache: dict[str, uuid.UUID]
) -> uuid.UUID:
    if email in cache:
        return cache[email]
    existing = (
        await session.execute(
            select(User.user_id).where(User.corporate_email == email)
        )
    ).scalar_one_or_none()
    if existing:
        cache[email] = existing
        return existing
    student = User(
        user_id=uuid.uuid4(),
        tenant_id=tenant_id,
        corporate_email=email,
        password_hash=pw_hash,
        assigned_role="Student",
        is_mfa_enabled=False,
    )
    session.add(student)
    await session.flush()
    cache[email] = student.user_id
    return student.user_id


async def _mark_failed(
    dataset_id: uuid.UUID, tenant_id: uuid.UUID, task_id: uuid.UUID, message: str
) -> None:
    try:
        async with async_session_maker() as session:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :t, true)"),
                {"t": str(tenant_id)},
            )
            dataset = await session.get(Dataset, dataset_id)
            if dataset is not None:
                dataset.processing_status = DatasetStatus.FAILED.value
            task = await session.get(BackgroundTask, task_id)
            if task is not None:
                task.status = TaskStatus.FAILED.value
                task.error = {"code": "CLEANING_ERROR", "message": message[:500]}
                task.completed_at = datetime.now(timezone.utc)
            await session.commit()
    except Exception:
        logger.exception("Failed to record cleaning failure for %s", dataset_id)

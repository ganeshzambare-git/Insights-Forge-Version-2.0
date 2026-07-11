"""Tenant-neutral, auditable educational dataset cleaning pipeline.

This module deliberately contains no database access.  It turns tabular input
into canonical rows, records every material decision, and returns clean,
review, and dead-letter partitions for callers to persist in their own UoW.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import re
from typing import Any, Iterable
from uuid import uuid4

import numpy as np
import pandas as pd

from app.ingestion.config import load_settings
from app.ingestion.normalizers.value_normalizer import (
    normalize_attendance,
    normalize_cgpa,
    normalize_email,
    normalize_marks,
    normalize_phone,
)

try:  # The pipeline remains usable in minimal installs without ML extras.
    from sklearn.ensemble import IsolationForest
    from sklearn.impute import KNNImputer
except ImportError:  # pragma: no cover - covered by the deterministic fallback
    IsolationForest = None  # type: ignore[assignment,misc]
    KNNImputer = None  # type: ignore[assignment,misc]

try:
    from rapidfuzz import process
except ImportError:  # pragma: no cover
    process = None  # type: ignore[assignment]


ALIASES = {
    "student_id": {"student id", "studentid", "roll no", "roll number", "id", "enrollment no"},
    "student_name": {"student name", "name", "full name", "student"},
    "email": {"email", "e mail", "e-mail", "student email", "corporate email"},
    "phone": {"phone", "mobile", "mobile number", "contact number", "phone number"},
    "course": {"course", "program", "programme", "degree"},
    "branch": {"branch", "department", "specialization", "specialisation"},
    "cohort": {"cohort", "cohort code", "class", "section", "batch"},
    "semester": {"semester", "sem", "term", "year of study"},
    "grade": {"raw average grade", "grade", "marks", "score", "average grade", "avg grade", "percentage"},
    "attendance": {"attendance", "attendance percentage", "attendance pct", "attendance %"},
    "cgpa": {"cgpa", "gpa", "cumulative gpa"},
    "reporting_period": {"reporting period", "period", "academic period"},
    "age": {"age"},
    "dob": {"dob", "date of birth", "birth date"},
    "gender": {"gender", "sex"},
    "category": {"category", "caste"},
    "credits": {"credits", "credits earned"},
    "backlogs": {"backlogs", "arrears"},
    "result_status": {"result", "result status", "status"},
}

COURSES = ("B.Tech", "B.E.", "B.Sc", "BCA", "BBA", "B.Com", "B.A.", "B.Arch", "MBA", "MCA", "M.Sc", "M.Tech", "M.E.", "M.Com", "M.A.", "Diploma", "PG Diploma", "Ph.D", "B.Tech + MBA", "B.Tech + M.Tech")
COURSE_LIMITS = {"B.Tech": 8, "B.E.": 8, "B.Sc": 6, "BCA": 6, "BBA": 6, "B.Com": 6, "MBA": 4, "MCA": 4, "M.Sc": 4, "M.Tech": 4, "Diploma": 6, "Ph.D": 12}
BRANCHES = ("Computer Science Engineering", "Information Technology", "Electronics & Communication Engineering", "Electrical & Electronics Engineering", "Mechanical Engineering", "Civil Engineering", "Artificial Intelligence & Data Science", "Biotechnology", "Chemical Engineering", "Computer Applications", "Computer Science", "Finance", "Marketing", "Human Resources", "Operations", "Business Analytics", "Management", "General", "Accounting", "Banking", "Taxation", "Physics", "Chemistry", "Mathematics", "Biology", "Statistics")
BRANCH_ALIASES = {"cse": "Computer Science Engineering", "cs": "Computer Science Engineering", "comp sci": "Computer Science Engineering", "computer science": "Computer Science Engineering", "computer engineering": "Computer Science Engineering", "it": "Information Technology", "info tech": "Information Technology", "ece": "Electronics & Communication Engineering", "electronics": "Electronics & Communication Engineering", "eee": "Electrical & Electronics Engineering", "electrical": "Electrical & Electronics Engineering", "me": "Mechanical Engineering", "mech": "Mechanical Engineering", "ce": "Civil Engineering", "civil eng": "Civil Engineering", "ai ds": "Artificial Intelligence & Data Science", "ai & ds": "Artificial Intelligence & Data Science", "ai": "Artificial Intelligence & Data Science", "data science": "Artificial Intelligence & Data Science", "biotech": "Biotechnology", "bio tech": "Biotechnology", "bt": "Biotechnology", "hr": "Human Resources", "hrm": "Human Resources", "ops": "Operations", "mkt": "Marketing", "fin": "Finance", "ba": "Business Analytics", "analytics": "Business Analytics", "comp app": "Computer Applications"}
EMAIL_DOMAINS = {"gmial.com": "gmail.com", "gamil.com": "gmail.com", "gmail.co": "gmail.com", "yhoo.com": "yahoo.com", "yahooo.com": "yahoo.com", "hotmal.com": "hotmail.com"}
COURSE_BRANCHES = {
    "B.Tech": {"Computer Science Engineering", "Information Technology", "Electronics & Communication Engineering", "Electrical & Electronics Engineering", "Mechanical Engineering", "Civil Engineering", "Artificial Intelligence & Data Science", "Biotechnology", "Chemical Engineering"},
    "B.E.": {"Computer Science Engineering", "Information Technology", "Electronics & Communication Engineering", "Electrical & Electronics Engineering", "Mechanical Engineering", "Civil Engineering", "Artificial Intelligence & Data Science", "Biotechnology", "Chemical Engineering"},
    "BCA": {"Computer Applications"}, "MCA": {"Computer Applications"},
    "MBA": {"Finance", "Marketing", "Human Resources", "Operations", "Business Analytics"},
}


@dataclass(frozen=True)
class AuditEvent:
    """One transparent cleaning decision, safe to serialize in a task result."""

    stage: str
    action: str
    count: int
    confidence: float
    detail: str


@dataclass
class PipelineResult:
    clean: pd.DataFrame
    review: pd.DataFrame
    dead_letter: pd.DataFrame
    audit: list[AuditEvent] = field(default_factory=list)
    column_map: dict[str, str] = field(default_factory=dict)

    @property
    def compliance(self) -> float:
        total = len(self.clean) + len(self.review) + len(self.dead_letter)
        return round((len(self.clean) / total) * 100, 2) if total else 0.0


def normalize_header(value: Any) -> str:
    """Normalize a header without destroying its semantic tokens."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value).lower())).strip()


def _best_match(value: str, choices: Iterable[str], threshold: int = 86) -> tuple[str | None, float]:
    normalized = normalize_header(value)
    direct = {normalize_header(item): item for item in choices}
    if normalized in direct:
        return direct[normalized], 1.0
    if process is not None:
        match = process.extractOne(normalized, direct.keys(), score_cutoff=load_settings()["thresholds"]["fuzzy_match"])
        if match:
            return direct[match[0]], round(match[1] / 100, 2)
    return None, 0.0


def recognize_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[AuditEvent]]:
    """Stage 0.5/1: remove truly empty columns and identify canonical fields."""
    frame = frame.copy()
    empty = [name for name in frame if frame[name].replace(r"^\s*$", np.nan, regex=True).isna().all()]
    if empty:
        frame = frame.drop(columns=empty)
    mapping: dict[str, str] = {}
    events = [AuditEvent("0.5", "dropped_empty_columns", len(empty), 1.0, ", ".join(map(str, empty)))] if empty else []
    for original in frame.columns:
        header = normalize_header(original)
        for canonical, names in ALIASES.items():
            if header == normalize_header(canonical) or header in names:
                if canonical not in mapping.values():
                    mapping[str(original)] = canonical
                break
    renamed = frame.rename(columns=mapping)
    events.append(AuditEvent("1", "recognized_columns", len(mapping), 0.98, str(mapping)))
    return renamed, mapping, events


def _append_reason(frame: pd.DataFrame, mask: pd.Series, reason: str, confidence: float) -> None:
    if not mask.any():
        return
    frame.loc[mask, "_reasons"] = frame.loc[mask, "_reasons"].map(lambda old: [*old, reason])
    frame.loc[mask, "_confidence"] = frame.loc[mask, "_confidence"].clip(upper=confidence)


def _normalize_recoverable_values(frame: pd.DataFrame) -> AuditEvent:
    """Normalize contacts and academic values before any rejecting validation."""
    normalizers = {
        "email": normalize_email,
        "phone": normalize_phone,
        "cgpa": normalize_cgpa,
        "grade": normalize_marks,
        "attendance": normalize_attendance,
    }
    changed = 0
    for column, normalizer in normalizers.items():
        if column not in frame:
            continue
        original = frame[column].copy()
        frame[column] = frame[column].map(normalizer)
        changed += int(original.astype(str).ne(frame[column].astype(str)).sum())
    return AuditEvent("3", "normalized_recoverable_values", changed, 0.95, "email, phone, CGPA, marks, attendance")


def _canonicalize_categories(frame: pd.DataFrame) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    if "course" in frame:
        values = frame["course"].fillna("").astype(str).str.strip()
        mapped = values.map(lambda value: _best_match(value, COURSES)[0] if value else None)
        invalid = values.ne("") & mapped.isna()
        frame.loc[mapped.notna(), "course"] = mapped[mapped.notna()]
        _append_reason(frame, invalid, "unrecognized_course", 0.55)
        events.append(AuditEvent("2", "standardized_courses", int(mapped.notna().sum()), 0.9, "course master"))
    if "branch" in frame:
        raw = frame["branch"].fillna("").astype(str).str.strip()
        normalized = raw.str.lower().map(BRANCH_ALIASES)
        fuzzy = raw.map(lambda value: _best_match(value, BRANCHES)[0] if value else None)
        mapped = normalized.fillna(fuzzy)
        invalid = raw.ne("") & mapped.isna()
        frame.loc[mapped.notna(), "branch"] = mapped[mapped.notna()]
        _append_reason(frame, invalid, "unrecognized_branch", 0.55)
        events.append(AuditEvent("2", "standardized_branches", int(mapped.notna().sum()), 0.9, "branch master"))
    return events


def _validate_contacts(frame: pd.DataFrame) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    if "email" in frame:
        email = frame["email"].fillna("").astype(str).str.strip().str.lower().str.replace(r"\s+", "", regex=True)
        corrected = email.map(lambda value: value.rsplit("@", 1)[0] + "@" + EMAIL_DOMAINS.get(value.rsplit("@", 1)[1], value.rsplit("@", 1)[1]) if value.count("@") == 1 else value)
        frame["email"] = corrected
        invalid = corrected.ne("") & ~corrected.str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", na=False)
        _append_reason(frame, invalid, "invalid_email", 0.45)
        events.append(AuditEvent("6", "validated_email", int((~invalid).sum()), 0.95, "format and known domain fixes"))
    if "phone" in frame:
        phone = frame["phone"].fillna("").astype(str).str.replace(r"\D", "", regex=True).str.replace(r"^(?:00)?91", "", regex=True)
        frame["phone"] = phone
        invalid = phone.ne("") & (~phone.str.fullmatch(r"[6-9]\d{9}", na=False))
        _append_reason(frame, invalid, "invalid_phone", 0.65)
        events.append(AuditEvent("6", "validated_phone", int((~invalid).sum()), 0.92, "Indian mobile normalization"))
    return events


def _validate_logic_and_demographics(frame: pd.DataFrame) -> list[AuditEvent]:
    """Stages 4/5: validate relationships and normalize demographic fields."""
    events: list[AuditEvent] = []
    if {"course", "branch"}.issubset(frame.columns):
        allowed = frame["course"].map(COURSE_BRANCHES)
        invalid = allowed.notna() & ~frame.apply(lambda row: row["branch"] in (COURSE_BRANCHES.get(row["course"], {row["branch"]})), axis=1)
        events.append(AuditEvent("4", "course_branch_anomalies_logged", int(invalid.sum()), 0.7, "non-blocking partner-program combinations"))
    if "age" in frame:
        age = pd.to_numeric(frame["age"], errors="coerce")
        invalid_age = age.notna() & ~age.between(16, 60)
        frame["age"] = age
        _append_reason(frame, invalid_age, "age_out_of_range", 0.45)
        events.append(AuditEvent("5", "validated_age", int((~invalid_age).sum()), 0.95, "age 16-60"))
    if "dob" in frame:
        dob = pd.to_datetime(frame["dob"], errors="coerce", utc=True)
        invalid_dob = dob.notna() & ((dob > pd.Timestamp.now(tz="UTC")) | (dob < pd.Timestamp("1900-01-01", tz="UTC")))
        frame["dob"] = dob.dt.strftime("%Y-%m-%d").where(dob.notna(), pd.NA)
        _append_reason(frame, invalid_dob, "invalid_dob", 0.4)
        events.append(AuditEvent("5", "validated_dob", int(dob.notna().sum()), 0.9, "ISO date"))
    for column_name, values in {"gender": {"m": "Male", "male": "Male", "f": "Female", "female": "Female", "other": "Other"}, "category": {"general": "General", "obc": "OBC", "sc": "SC", "st": "ST", "ews": "EWS"}}.items():
        if column_name in frame:
            raw = frame[column_name].fillna("").astype(str).str.strip().str.lower()
            mapped = raw.map(values)
            invalid = raw.ne("") & mapped.isna()
            frame.loc[mapped.notna(), column_name] = mapped[mapped.notna()]
            _append_reason(frame, invalid, f"invalid_{column_name}", 0.55)
    return events


def _validate_academics(frame: pd.DataFrame) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    for column, lower, upper in (("grade", 0, 100), ("attendance", 0, 100), ("cgpa", 0, 10)):
        if column not in frame:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        severe = numeric.lt(lower) | numeric.gt(upper + (5 if column != "cgpa" else 0.5))
        clampable = numeric.gt(upper) & ~severe
        numeric.loc[clampable] = upper
        frame[column] = numeric
        _append_reason(frame, severe.fillna(False), f"{column}_out_of_range", 0.35)
        events.append(AuditEvent("7", f"validated_{column}", int(numeric.notna().sum()), 0.98, f"range {lower}-{upper}"))
    if "semester" in frame:
        semester = pd.to_numeric(frame["semester"], errors="coerce")
        frame["semester"] = semester
        if "course" in frame:
            maximum = frame["course"].map(COURSE_LIMITS)
            _append_reason(frame, (semester.lt(1) | semester.gt(maximum)).fillna(False), "semester_out_of_range", 0.5)
    return events


def _deduplicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, AuditEvent]:
    keys = [key for key in ("student_id", "email", "student_name", "semester", "reporting_period") if key in frame]
    if not keys:
        return frame, frame.iloc[0:0].copy(), AuditEvent("8", "deduplicated", 0, 1.0, "no identity columns")
    completeness = frame.notna().sum(axis=1)
    ordered = frame.assign(_completeness=completeness).sort_values("_completeness", ascending=False)
    duplicates = ordered.duplicated(subset=keys, keep="first")
    rejected = ordered.loc[duplicates].drop(columns="_completeness")
    clean = ordered.loc[~duplicates].drop(columns="_completeness")
    return clean, rejected, AuditEvent("8", "deduplicated", int(duplicates.sum()), 0.98, f"keys={keys}")


def _impute(frame: pd.DataFrame) -> AuditEvent:
    numeric = [name for name in ("grade", "attendance", "cgpa", "semester", "credits") if name in frame]
    if not numeric:
        return AuditEvent("9", "imputed_numeric", 0, 1.0, "no numeric canonical fields")
    before = int(frame[numeric].isna().sum().sum())
    if before and KNNImputer is not None and len(frame) > 1:
        frame[numeric] = KNNImputer(n_neighbors=min(5, len(frame))).fit_transform(frame[numeric])
    else:
        frame[numeric] = frame[numeric].fillna(frame[numeric].median(numeric_only=True))
    return AuditEvent("9", "imputed_numeric", before, 0.85, "KNN or median fallback")


def _outliers(frame: pd.DataFrame) -> tuple[pd.Series, AuditEvent]:
    numeric = [name for name in ("grade", "attendance", "cgpa") if name in frame and frame[name].notna().any()]
    flagged = pd.Series(False, index=frame.index)
    if len(numeric) >= 1 and len(frame) >= 20 and IsolationForest is not None:
        values = frame[numeric].fillna(frame[numeric].median()).to_numpy()
        flagged = pd.Series(IsolationForest(contamination=0.01, random_state=42).fit_predict(values) == -1, index=frame.index)
    return flagged, AuditEvent("10", "statistical_outliers", int(flagged.sum()), 0.85, "IsolationForest when sample is sufficient")


def run_cleaning_pipeline(frame: pd.DataFrame, *, preserve_source_headers: bool = True) -> PipelineResult:
    """Run stages 0.5–10 and return clean, review, and dead-letter partitions.

    Unknown columns are retained.  Required fields are inferred from the input
    contract: a narrow analytics upload needs email/cohort/grade/attendance,
    while a student registry additionally requires student identity and course.
    """
    if frame.empty:
        return PipelineResult(frame.copy(), frame.copy(), frame.copy(), [AuditEvent("0", "empty_dataset", 0, 1.0, "no records")])
    work, mapping, audit = recognize_columns(frame)
    work["_record_id"] = [str(uuid4()) for _ in range(len(work))]
    work["_reasons"] = [[] for _ in range(len(work))]
    work["_confidence"] = 1.0
    audit.append(_normalize_recoverable_values(work))
    audit.extend(_canonicalize_categories(work))
    audit.extend(_validate_logic_and_demographics(work))
    audit.extend(_validate_contacts(work))
    audit.extend(_validate_academics(work))
    work, duplicates, event = _deduplicate(work)
    audit.append(event)
    audit.append(_impute(work))
    outliers, event = _outliers(work)
    audit.append(event)
    _append_reason(work, outliers, "statistical_outlier", 0.65)
    required = [name for name in load_settings()["dead_letter"]["critical_fields"] if name in work]
    missing = work[required].isna().any(axis=1) if required else pd.Series(False, index=work.index)
    _append_reason(work, missing, "missing_required_field", 0.0)
    dead = missing
    review = ~dead & work["_reasons"].map(bool)
    dead_frame = pd.concat([duplicates, work.loc[dead]], ignore_index=True)
    result = PipelineResult(work.loc[~dead & ~review].reset_index(drop=True), work.loc[review].reset_index(drop=True), dead_frame.reset_index(drop=True), audit, mapping)
    if preserve_source_headers:
        inverse = {canonical: source for source, canonical in mapping.items()}
        def restore(partition: pd.DataFrame) -> pd.DataFrame:
            return partition.rename(columns=inverse)
        result.clean, result.review, result.dead_letter = (restore(result.clean), restore(result.review), restore(result.dead_letter))
    return result


def create_review_queue(result: PipelineResult) -> pd.DataFrame:
    """Create a durable, serializable queue payload for human review tooling."""
    queue = result.review.copy()
    if queue.empty:
        return queue
    queue["review_status"] = "Pending"
    queue["priority"] = queue["_reasons"].map(lambda reasons: "High" if len(reasons) >= 2 else "Medium")
    queue["assigned_to"] = pd.NA
    queue["queued_at"] = datetime.now(UTC).isoformat()
    return queue


def process_review_decision(record: dict[str, Any], decision: str, corrections: dict[str, Any] | None = None) -> dict[str, Any]:
    """Apply an explicit reviewer decision without silently overwriting data."""
    normalized = decision.strip().lower()
    if normalized not in {"accept", "edit", "revert", "reject", "second_review"}:
        raise ValueError("Unsupported review decision")
    updated = dict(record)
    if normalized == "edit":
        if not corrections:
            raise ValueError("Corrections are required for an edit decision")
        updated.update(corrections)
    updated["review_status"] = {"accept": "Validated", "edit": "Validated", "revert": "Reverted", "reject": "Rejected", "second_review": "Second Review"}[normalized]
    updated["reviewed_at"] = datetime.now(UTC).isoformat()
    if normalized in {"accept", "edit", "revert"}:
        updated["_confidence"] = 1.0
        updated["_reasons"] = []
    return updated

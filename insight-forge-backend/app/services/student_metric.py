"""
Insight Forge V2 — Student Metric Service.

Orchestrates academic performance and attendance metric logging and validation.
"""

from decimal import Decimal
import uuid
from typing import Any, Sequence

from sqlalchemy import func, select

from app.models.student_metric import StudentMetric
from app.models.cohort import Cohort
from app.models.user import User
from app.repositories.student_metric import StudentMetricRepository
from app.repositories.user import UserRepository
from app.repositories.cohort import CohortRepository
from app.repositories.tenant import TenantRepository
from app.services.academic_mapping import (
    grade_to_gpa,
    grade_to_letter,
    status_to_risk,
)
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import ValidationError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class StudentMetricService(BaseService):
    """Business service governing StudentMetric lifecycle rules."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the StudentMetricService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = StudentMetricRepository(session=uow.session)
        self.user_repo = UserRepository(session=uow.session)
        self.cohort_repo = CohortRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)
        self.allowed_statuses = {"Safe", "Amber", "Critical"}

    async def add_metric(
        self,
        tenant_id: uuid.UUID,
        student_user_id: uuid.UUID,
        cohort_id: uuid.UUID,
        raw_average_grade: Decimal,
        normalized_grade_score: Decimal | None,
        attendance_percentage: Decimal,
        success_indicator_status: str,
        reporting_period: str,
    ) -> ServiceResult[StudentMetric]:
        """Log a new academic performance and attendance record.

        Args:
            tenant_id: Tenant UUID partition scope.
            student_user_id: Student user UUID.
            cohort_id: Cohort UUID.
            raw_average_grade: Raw average grade value.
            normalized_grade_score: Optional normalized grade.
            attendance_percentage: Attendance percent.
            success_indicator_status: Success label.
            reporting_period: Academic reporting period string.

        Returns:
            A ServiceResult wrapping the created StudentMetric entity.
        """

        async def action() -> StudentMetric:
            await self._validate_add_request(
                tenant_id,
                student_user_id,
                cohort_id,
                raw_average_grade,
                attendance_percentage,
                success_indicator_status,
                reporting_period,
            )

            metric = StudentMetric(
                tenant_id=tenant_id,
                student_user_id=student_user_id,
                cohort_id=cohort_id,
                raw_average_grade=raw_average_grade,
                normalized_grade_score=normalized_grade_score,
                attendance_percentage=attendance_percentage,
                success_indicator_status=success_indicator_status,
                reporting_period=reporting_period.strip(),
            )
            created = await self.repo.create(metric)
            self.publish_domain_event(
                "MetricRecorded",
                {"metric_id": created.metric_id, "student_id": str(student_user_id)},
            )
            return created

        return await self.execute_command(
            "add_metric",
            action,
            success_msg=f"Metric logged successfully for student '{student_user_id}'.",
        )

    async def get_metric(self, metric_id: int) -> StudentMetric | None:
        """Fetch a single student metric record by ID.

        Args:
            metric_id: Target metric ID.

        Returns:
            The StudentMetric entity if found, otherwise None.
        """
        return await self.repo.get_by_id(metric_id)

    async def get_metrics(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> Sequence[StudentMetric]:
        """Fetch all metric history for a specific student (tenant-scoped).

        Args:
            tenant_id: Tenant UUID partition scope.
            student_id: Target student UUID.

        Returns:
            A sequence of StudentMetric records.
        """
        return await self.repo.get_by_student(tenant_id, student_id)

    async def latest_metrics(
        self, tenant_id: uuid.UUID, limit: int = 100
    ) -> Sequence[StudentMetric]:
        """Fetch the most recent metrics inside a tenant (tenant-scoped).

        Args:
            tenant_id: Tenant UUID partition scope.
            limit: Maximum records count.

        Returns:
            A sequence of StudentMetric records.
        """
        return await self.repo.get_latest_metrics(tenant_id, limit)

    # ============================================================
    # Read models for dashboards (real aggregates over student_metrics)
    # ============================================================

    @staticmethod
    def _display_name(email: str) -> str:
        """Derive a human-ish display name from an email local-part."""
        local = (email or "").split("@")[0]
        parts = [p for p in local.replace(".", " ").replace("_", " ").split() if p]
        return " ".join(p.capitalize() for p in parts) or email

    async def _latest_metric_per_student(
        self, tenant_id: uuid.UUID, *, cohort_id: uuid.UUID | None = None
    ) -> list[tuple[StudentMetric, str]]:
        """Return each student's most recent metric (optionally within a cohort).

        Returns a list of ``(StudentMetric, corporate_email)`` tuples.
        """
        session = self.uow.session
        stmt = (
            select(StudentMetric, User.corporate_email)
            .join(User, StudentMetric.student_user_id == User.user_id)
            .where(StudentMetric.tenant_id == tenant_id)
            .order_by(StudentMetric.metric_id.asc())
        )
        if cohort_id is not None:
            stmt = stmt.where(StudentMetric.cohort_id == cohort_id)

        result = await session.execute(stmt)
        latest: dict[uuid.UUID, tuple[StudentMetric, str]] = {}
        for metric, email in result.all():
            latest[metric.student_user_id] = (metric, email)  # asc order -> last wins
        return list(latest.values())

    async def cohort_roster(
        self, tenant_id: uuid.UUID, cohort_id: uuid.UUID, search: str | None = None
    ) -> list[dict[str, Any]]:
        """Build a roster of students in a cohort from their latest metric."""
        rows = await self._latest_metric_per_student(tenant_id, cohort_id=cohort_id)
        roster: list[dict[str, Any]] = []
        for metric, email in rows:
            name = self._display_name(email)
            roster.append(
                {
                    "id": str(metric.student_user_id),
                    "name": name,
                    "email": email,
                    "gpa": grade_to_gpa(metric.raw_average_grade),
                    "status": "Enrolled",
                    "risk_level": status_to_risk(metric.success_indicator_status),
                }
            )
        if search:
            q = search.lower()
            roster = [
                r
                for r in roster
                if q in r["name"].lower() or q in r["email"].lower()
            ]
        roster.sort(key=lambda r: r["name"])
        return roster

    async def attendance_trend(
        self,
        tenant_id: uuid.UUID,
        semester: str | None = None,
        cohort_code: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate average attendance by reporting period (real trend)."""
        session = self.uow.session
        stmt = (
            select(
                StudentMetric.reporting_period,
                Cohort.cohort_code,
                func.avg(StudentMetric.attendance_percentage),
            )
            .join(Cohort, StudentMetric.cohort_id == Cohort.cohort_id)
            .where(StudentMetric.tenant_id == tenant_id)
            .group_by(StudentMetric.reporting_period, Cohort.cohort_code)
            .order_by(StudentMetric.reporting_period.asc())
        )
        if semester:
            stmt = stmt.where(StudentMetric.reporting_period == semester)
        if cohort_code:
            stmt = stmt.where(Cohort.cohort_code == cohort_code)

        result = await session.execute(stmt)
        trend = [
            {
                "month": period,
                "attendance_rate": round(float(avg), 2),
                "cohort": code,
                "semester": period,
            }
            for period, code, avg in result.all()
        ]
        values = [t["attendance_rate"] for t in trend]
        summary = {
            "average_attendance_rate": round(sum(values) / len(values), 2)
            if values
            else 0.0,
            "peak_attendance_rate": max(values) if values else 0.0,
            "trough_attendance_rate": min(values) if values else 0.0,
            "total_months": len(trend),
        }
        return {"trend": trend, "summary": summary}

    async def department_records(
        self, tenant_id: uuid.UUID, scope: str
    ) -> list[dict[str, Any]]:
        """List students whose cohort belongs to a department scope."""
        session = self.uow.session
        stmt = (
            select(StudentMetric, User.corporate_email, Cohort.department_scope)
            .join(User, StudentMetric.student_user_id == User.user_id)
            .join(Cohort, StudentMetric.cohort_id == Cohort.cohort_id)
            .where(StudentMetric.tenant_id == tenant_id)
            .order_by(StudentMetric.metric_id.asc())
        )
        if scope:
            stmt = stmt.where(Cohort.department_scope.ilike(f"%{scope}%"))

        result = await session.execute(stmt)
        latest: dict[uuid.UUID, dict[str, Any]] = {}
        for metric, email, department in result.all():
            latest[metric.student_user_id] = {
                "id": str(metric.student_user_id),
                "name": self._display_name(email),
                "department": department,
                "term_gpa": grade_to_gpa(metric.raw_average_grade),
                "risk_level": status_to_risk(metric.success_indicator_status),
                "term_credits": 15,
                "status": "Enrolled",
            }
        records = list(latest.values())
        records.sort(key=lambda r: r["name"])
        return records

    async def student_progress(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID, term: str | None = None
    ) -> dict[str, Any]:
        """Build a student's progress summary from their metrics."""
        metrics = list(await self.repo.get_by_student(tenant_id, student_id))
        metrics.sort(key=lambda m: m.metric_id)
        if term:
            scoped = [m for m in metrics if m.reporting_period == term]
            if scoped:
                metrics = scoped

        if not metrics:
            return {
                "gpa": 0.0,
                "attendance_rate": 0,
                "ledger_empty": True,
                "records": [],
                "attendance_history": [],
                "study_modules": [],
                "term": term,
            }

        latest = metrics[-1]
        # One record per cohort the student has a metric in (subject == cohort).
        records = []
        for m in metrics:
            cohort = await self.cohort_repo.get_by_id(m.cohort_id)
            subject = cohort.cohort_code if cohort else str(m.cohort_id)
            records.append(
                {
                    "subject": subject,
                    "grade": grade_to_letter(m.raw_average_grade),
                    "score": float(m.raw_average_grade),
                }
            )

        return {
            "gpa": grade_to_gpa(latest.raw_average_grade),
            "attendance_rate": round(float(latest.attendance_percentage)),
            "ledger_empty": False,
            "records": records,
            "attendance_history": [],
            "study_modules": [],
            "term": term or latest.reporting_period,
        }

    async def student_gpa_history(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> dict[str, Any]:
        """Return the student's GPA trend and their cohort's average trend."""
        metrics = list(await self.repo.get_by_student(tenant_id, student_id))
        metrics.sort(key=lambda m: m.metric_id)

        student_history = [
            {"label": m.reporting_period, "val": grade_to_gpa(m.raw_average_grade)}
            for m in metrics
        ]

        # Cohort average GPA per reporting period (across the student's cohorts).
        cohort_history: list[dict[str, Any]] = []
        cohort_ids = {m.cohort_id for m in metrics}
        if cohort_ids:
            session = self.uow.session
            stmt = (
                select(
                    StudentMetric.reporting_period,
                    func.avg(StudentMetric.raw_average_grade),
                )
                .where(
                    StudentMetric.tenant_id == tenant_id,
                    StudentMetric.cohort_id.in_(cohort_ids),
                )
                .group_by(StudentMetric.reporting_period)
                .order_by(StudentMetric.reporting_period.asc())
            )
            result = await session.execute(stmt)
            cohort_history = [
                {"label": period, "val": grade_to_gpa(avg)}
                for period, avg in result.all()
            ]

        return {
            "student_gpa_history": student_history,
            "cohort_gpa_history": cohort_history,
        }

    async def tenant_baseline(self, tenant_id: uuid.UUID) -> dict[str, Any]:
        """Compute the tenant's current average GPA/attendance baseline."""
        session = self.uow.session
        stmt = select(
            func.avg(StudentMetric.raw_average_grade),
            func.avg(StudentMetric.attendance_percentage),
            func.count(func.distinct(StudentMetric.student_user_id)),
        ).where(StudentMetric.tenant_id == tenant_id)
        avg_grade, avg_attend, students = (await session.execute(stmt)).one()

        return {
            "avg_gpa": grade_to_gpa(avg_grade) if avg_grade is not None else 0.0,
            "avg_grade": round(float(avg_grade), 2) if avg_grade is not None else 0.0,
            "avg_attendance": round(float(avg_attend), 2)
            if avg_attend is not None
            else 0.0,
            "student_count": int(students or 0),
        }

    async def course_evaluation(
        self,
        tenant_id: uuid.UUID,
        department: str | None = None,
        cohort_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Derive course-like performance rows from cohorts + their metrics.

        Each cohort is treated as a course/programme: average score, pass rate
        (grade >= 60), and enrolment come from the latest metric per student.
        """
        session = self.uow.session
        cohort_stmt = select(Cohort).where(Cohort.tenant_id == tenant_id)
        if department:
            cohort_stmt = cohort_stmt.where(
                Cohort.department_scope.ilike(f"%{department}%")
            )
        if cohort_code:
            cohort_stmt = cohort_stmt.where(Cohort.cohort_code == cohort_code)
        cohorts = (await session.execute(cohort_stmt)).scalars().all()

        courses: list[dict[str, Any]] = []
        for cohort in cohorts:
            rows = await self._latest_metric_per_student(
                tenant_id, cohort_id=cohort.cohort_id
            )
            scores = [float(m.raw_average_grade) for m, _ in rows]
            enrollment = len(scores)
            if enrollment:
                avg_score = round(sum(scores) / enrollment, 2)
                pass_rate = round(
                    sum(1 for s in scores if s >= 60) / enrollment * 100, 2
                )
            else:
                avg_score = 0.0
                pass_rate = 0.0

            if avg_score >= 85:
                kpi = "Exceeding"
            elif avg_score >= 70:
                kpi = "On Track"
            else:
                kpi = "At Risk"

            courses.append(
                {
                    "course_id": cohort.cohort_code,
                    "course_name": f"{cohort.department_scope} Programme",
                    "department": cohort.department_scope,
                    "cohort_code": cohort.cohort_code,
                    "avg_score": avg_score,
                    "pass_rate": pass_rate,
                    "enrollment": enrollment,
                    "evaluations_submitted": enrollment,
                    "kpi_status": kpi,
                }
            )
        courses.sort(key=lambda c: c["course_id"])
        return courses

    async def update_metric(
        self,
        metric_id: int,
        raw_average_grade: Decimal | None = None,
        normalized_grade_score: Decimal | None = None,
        attendance_percentage: Decimal | None = None,
        success_indicator_status: str | None = None,
        reporting_period: str | None = None,
    ) -> ServiceResult[StudentMetric]:
        """Update metrics parameters.

        Args:
            metric_id: Target metric ID.
            raw_average_grade: Updated grade.
            normalized_grade_score: Updated normalized grade.
            attendance_percentage: Updated attendance.
            success_indicator_status: Updated success indicator status.
            reporting_period: Updated reporting period.

        Returns:
            A ServiceResult wrapping the updated StudentMetric entity.
        """

        async def action() -> StudentMetric:
            metric = await self.repo.get_by_id(metric_id)
            if not metric:
                raise NotFoundError(
                    f"Student metric with ID '{metric_id}' not found.",
                    error_code="metric_not_found",
                )

            updates = {}
            if raw_average_grade is not None:
                self._validate_grade(raw_average_grade)
                updates["raw_average_grade"] = raw_average_grade
            if normalized_grade_score is not None:
                updates["normalized_grade_score"] = normalized_grade_score
            if attendance_percentage is not None:
                self._validate_attendance(attendance_percentage)
                updates["attendance_percentage"] = attendance_percentage
            if success_indicator_status is not None:
                self._validate_status(success_indicator_status)
                updates["success_indicator_status"] = success_indicator_status
            if reporting_period is not None:
                if not reporting_period.strip():
                    raise ValidationError(
                        "Reporting period cannot be empty.",
                        error_code="period_required",
                    )
                updates["reporting_period"] = reporting_period.strip()

            updated = await self.repo.update(metric, **updates)
            return updated

    async def delete_metric(self, metric_id: int) -> ServiceResult[None]:
        """Delete a student metric record.

        Args:
            metric_id: Target metric ID.

        Returns:
            A ServiceResult indicating deletion status.
        """

        async def action() -> None:
            metric = await self.repo.get_by_id(metric_id)
            if not metric:
                raise NotFoundError(
                    f"Student metric with ID '{metric_id}' not found.",
                    error_code="metric_not_found",
                )
            await self.repo.delete(metric)

        return await self.execute_command(
            "delete_metric",
            action,
            success_msg=f"Student metric '{metric_id}' deleted successfully.",
        )

    # Private Helpers
    async def _validate_add_request(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        cohort_id: uuid.UUID,
        grade: Decimal,
        attendance: Decimal,
        status: str,
        period: str,
    ) -> None:
        if not period.strip():
            raise ValidationError(
                "Reporting period cannot be empty.", error_code="period_required"
            )
        self._validate_grade(grade)
        self._validate_attendance(attendance)
        self._validate_status(status)

        # Validate tenant exists
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.", error_code="tenant_not_found"
            )

        # Validate cohort exists and belongs to the tenant
        cohort = await self.cohort_repo.get_by_id(cohort_id)
        if not cohort or cohort.tenant_id != tenant_id:
            raise ValidationError(
                f"Cohort '{cohort_id}' does not exist or belong to tenant '{tenant_id}'.",
                error_code="cohort_tenant_mismatch",
            )

        # Validate student exists and belongs to the tenant
        student = await self.user_repo.get_by_id(student_id)
        if not student or student.tenant_id != tenant_id:
            raise ValidationError(
                f"Student user '{student_id}' does not exist or belong to tenant '{tenant_id}'.",
                error_code="student_tenant_mismatch",
            )

    def _validate_grade(self, grade: Decimal) -> None:
        if grade < Decimal("0.00") or grade > Decimal("100.00"):
            raise ValidationError(
                "Raw average grade must be between 0.00 and 100.00.",
                error_code="invalid_grade",
            )

    def _validate_attendance(self, attendance: Decimal) -> None:
        if attendance < Decimal("0.00") or attendance > Decimal("100.00"):
            raise ValidationError(
                "Attendance percentage must be between 0.00 and 100.00.",
                error_code="invalid_attendance",
            )

    def _validate_status(self, status: str) -> None:
        if status not in self.allowed_statuses:
            raise ValidationError(
                f"Status '{status}' is invalid. Allowed statuses: {self.allowed_statuses}",
                error_code="invalid_status",
            )

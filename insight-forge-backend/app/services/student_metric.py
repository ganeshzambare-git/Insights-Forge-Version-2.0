"""
Insight Forge V2 — Student Metric Service.

Orchestrates academic performance and attendance metric logging and validation.
"""

from decimal import Decimal
import uuid
from typing import Sequence
from app.models.student_metric import StudentMetric
from app.repositories.student_metric import StudentMetricRepository
from app.repositories.user import UserRepository
from app.repositories.cohort import CohortRepository
from app.repositories.tenant import TenantRepository
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

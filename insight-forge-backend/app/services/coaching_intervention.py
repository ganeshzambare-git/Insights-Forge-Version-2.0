"""
Insight Forge V2 — Coaching Intervention Service.

Orchestrates academic intervention logging, faculty validation, and isolation policies.
"""

import uuid
from typing import Sequence
from app.models.coaching_intervention import CoachingIntervention
from app.repositories.coaching_intervention import CoachingInterventionRepository
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import ValidationError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class CoachingInterventionService(BaseService):
    """Business service governing CoachingIntervention lifecycle rules."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the CoachingInterventionService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = CoachingInterventionRepository(session=uow.session)
        self.user_repo = UserRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)
        self.faculty_roles = {"Faculty", "Dean"}

    async def create_intervention(
        self,
        tenant_id: uuid.UUID,
        student_user_id: uuid.UUID,
        faculty_user_id: uuid.UUID,
        intervention_notes: str,
    ) -> ServiceResult[CoachingIntervention]:
        """Record a new student coaching intervention.

        Args:
            tenant_id: Scope Tenant UUID.
            student_user_id: Target student user UUID.
            faculty_user_id: Originating faculty user UUID.
            intervention_notes: Descriptive notes of the intervention session.

        Returns:
            A ServiceResult wrapping the created CoachingIntervention entity.
        """

        async def action() -> CoachingIntervention:
            await self._validate_create_request(
                tenant_id, student_user_id, faculty_user_id, intervention_notes
            )

            intervention = CoachingIntervention(
                intervention_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                student_user_id=student_user_id,
                faculty_user_id=faculty_user_id,
                intervention_notes=intervention_notes.strip(),
                recorded_timestamp=self.clock.now(),
            )
            created = await self.repo.create(intervention)
            self.publish_domain_event(
                "InterventionAdded",
                {
                    "intervention_id": str(created.intervention_id),
                    "student_id": str(student_user_id),
                },
            )
            return created

        return await self.execute_command(
            "create_intervention",
            action,
            success_msg=f"Coaching intervention created successfully for student '{student_user_id}'.",
        )

    async def get_intervention(
        self, intervention_id: uuid.UUID
    ) -> CoachingIntervention | None:
        """Fetch a single coaching intervention log by ID.

        Args:
            intervention_id: Coaching intervention UUID.

        Returns:
            The CoachingIntervention entity if found, otherwise None.
        """
        return await self.repo.get_by_id(intervention_id)

    async def get_interventions_by_student(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> Sequence[CoachingIntervention]:
        """Fetch all intervention history logged for a student (tenant-scoped).

        Args:
            tenant_id: Scope Tenant UUID.
            student_id: Target student UUID.

        Returns:
            A sequence of CoachingIntervention records.
        """
        return await self.repo.get_by_student(tenant_id, student_id)

    async def get_recent_interventions(
        self, tenant_id: uuid.UUID, limit: int = 50
    ) -> Sequence[CoachingIntervention]:
        """Fetch the most recent interventions (tenant-scoped).

        Args:
            tenant_id: Scope Tenant UUID.
            limit: Maximum count limit.

        Returns:
            A sequence of CoachingIntervention records.
        """
        return await self.repo.get_recent_interventions(tenant_id, limit)

    async def update_intervention(
        self, intervention_id: uuid.UUID, intervention_notes: str
    ) -> ServiceResult[CoachingIntervention]:
        """Update notes of an existing intervention.

        Args:
            intervention_id: Target intervention UUID.
            intervention_notes: New descriptive notes.

        Returns:
            A ServiceResult wrapping the updated CoachingIntervention entity.
        """

        async def action() -> CoachingIntervention:
            if not intervention_notes.strip():
                raise ValidationError(
                    "Intervention notes cannot be empty.", error_code="notes_required"
                )

            intervention = await self.repo.get_by_id(intervention_id)
            if not intervention:
                raise NotFoundError(
                    f"Coaching intervention with ID '{intervention_id}' not found.",
                    error_code="intervention_not_found",
                )

            updated = await self.repo.update(
                intervention, intervention_notes=intervention_notes.strip()
            )
            return updated

        return await self.execute_command(
            "update_intervention",
            action,
            success_msg=f"Intervention '{intervention_id}' updated successfully.",
        )

    async def delete_intervention(
        self, intervention_id: uuid.UUID
    ) -> ServiceResult[None]:
        """Delete an intervention log.

        Args:
            intervention_id: Target intervention UUID.

        Returns:
            A ServiceResult indicating deletion status.
        """

        async def action() -> None:
            intervention = await self.repo.get_by_id(intervention_id)
            if not intervention:
                raise NotFoundError(
                    f"Coaching intervention with ID '{intervention_id}' not found.",
                    error_code="intervention_not_found",
                )
            await self.repo.delete(intervention)

        return await self.execute_command(
            "delete_intervention",
            action,
            success_msg=f"Intervention '{intervention_id}' deleted successfully.",
        )

    # Private Helpers
    async def _validate_create_request(
        self,
        tenant_id: uuid.UUID,
        student_id: uuid.UUID,
        faculty_id: uuid.UUID,
        notes: str,
    ) -> None:
        if not notes.strip():
            raise ValidationError(
                "Intervention notes cannot be empty.", error_code="notes_required"
            )

        # Validate tenant exists
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.", error_code="tenant_not_found"
            )

        # Validate student user belongs to tenant and is a Student
        student = await self.user_repo.get_by_id(student_id)
        if not student or student.tenant_id != tenant_id:
            raise ValidationError(
                f"Student user '{student_id}' does not belong to tenant '{tenant_id}'.",
                error_code="student_tenant_mismatch",
            )
        if student.assigned_role != "Student":
            raise ValidationError(
                f"User '{student_id}' is not registered under Student role (Role: '{student.assigned_role}').",
                error_code="invalid_student_role",
            )

        # Validate faculty user belongs to tenant and has Faculty/Dean role
        faculty = await self.user_repo.get_by_id(faculty_id)
        if not faculty or faculty.tenant_id != tenant_id:
            raise ValidationError(
                f"Faculty user '{faculty_id}' does not belong to tenant '{tenant_id}'.",
                error_code="faculty_tenant_mismatch",
            )
        if faculty.assigned_role not in self.faculty_roles:
            raise ValidationError(
                f"User '{faculty_id}' is not registered under an advising role (Role: '{faculty.assigned_role}').",
                error_code="invalid_faculty_role",
            )

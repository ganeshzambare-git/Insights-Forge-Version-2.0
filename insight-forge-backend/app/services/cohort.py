"""
Insight Forge V2 — Cohort Service.

Orchestrates cohorts creation, lookup, updates, and validations.
"""

import uuid
from typing import Sequence
from app.models.cohort import Cohort
from app.repositories.cohort import CohortRepository
from app.repositories.tenant import TenantRepository
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import ValidationError, ConflictError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class CohortService(BaseService):
    """Business service governing Cohort lifecycle rules."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the CohortService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = CohortRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)

    async def create_cohort(
        self, tenant_id: uuid.UUID, cohort_code: str, department_scope: str
    ) -> ServiceResult[Cohort]:
        """Create a new cohort within a tenant.

        Args:
            tenant_id: Scope Tenant UUID.
            cohort_code: Unique code identifier for the cohort.
            department_scope: Department label mapping.

        Returns:
            A ServiceResult wrapping the created Cohort entity.
        """
        normalized_code = cohort_code.strip().upper()

        async def action() -> Cohort:
            await self._validate_create_request(
                tenant_id, normalized_code, department_scope
            )
            await self._validate_create_business_rules(tenant_id, normalized_code)

            cohort = Cohort(
                cohort_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                cohort_code=normalized_code,
                department_scope=department_scope.strip(),
            )
            created = await self.repo.create(cohort)
            self.publish_domain_event(
                "CohortCreated",
                {"cohort_id": str(created.cohort_id), "tenant_id": str(tenant_id)},
            )
            return created

        return await self.execute_command(
            "create_cohort",
            action,
            success_msg=f"Cohort '{normalized_code}' created successfully.",
        )

    async def get_cohort(self, cohort_id: uuid.UUID) -> Cohort | None:
        """Fetch a single Cohort by ID.

        Args:
            cohort_id: Cohort UUID.

        Returns:
            The Cohort entity if found, otherwise None.
        """
        return await self.repo.get_by_id(cohort_id)

    async def list_cohorts(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[Cohort]:
        """List all cohorts belonging to a specific tenant (tenant-scoped).

        Args:
            tenant_id: Scope Tenant UUID.
            limit: Maximum number of records to return.
            offset: Offset skip count.

        Returns:
            A sequence of Cohort entities.
        """
        return await self.repo.get_all(tenant_id=tenant_id, limit=limit, offset=offset)

    async def update_cohort(
        self,
        cohort_id: uuid.UUID,
        cohort_code: str | None = None,
        department_scope: str | None = None,
    ) -> ServiceResult[Cohort]:
        """Update Cohort code or department fields.

        Args:
            cohort_id: Target Cohort UUID.
            cohort_code: New cohort code.
            department_scope: New department scope.

        Returns:
            A ServiceResult wrapping the updated Cohort entity.
        """

        async def action() -> Cohort:
            cohort = await self.repo.get_by_id(cohort_id)
            if not cohort:
                raise NotFoundError(
                    f"Cohort with ID '{cohort_id}' not found.",
                    error_code="cohort_not_found",
                )

            updates = {}
            if cohort_code is not None:
                normalized_code = cohort_code.strip().upper()
                await self._validate_update_business_rules(
                    cohort.tenant_id, cohort_id, normalized_code
                )
                updates["cohort_code"] = normalized_code
            if department_scope is not None:
                updates["department_scope"] = department_scope.strip()

            updated = await self.repo.update(cohort, **updates)
            return updated

        return await self.execute_command(
            "update_cohort",
            action,
            success_msg=f"Cohort '{cohort_id}' updated successfully.",
        )

    async def delete_cohort(self, cohort_id: uuid.UUID) -> ServiceResult[None]:
        """Delete a cohort record.

        Args:
            cohort_id: Target Cohort UUID.

        Returns:
            A ServiceResult indicating deletion status.
        """

        async def action() -> None:
            cohort = await self.repo.get_by_id(cohort_id)
            if not cohort:
                raise NotFoundError(
                    f"Cohort with ID '{cohort_id}' not found.",
                    error_code="cohort_not_found",
                )
            await self.repo.delete(cohort)

        return await self.execute_command(
            "delete_cohort",
            action,
            success_msg=f"Cohort '{cohort_id}' deleted successfully.",
        )

    # Private Helpers
    async def _validate_create_request(
        self, tenant_id: uuid.UUID, code: str, department: str
    ) -> None:
        if not code.strip():
            raise ValidationError(
                "Cohort code cannot be empty.", error_code="code_required"
            )
        if not department.strip():
            raise ValidationError(
                "Department scope cannot be empty.", error_code="department_required"
            )
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.", error_code="tenant_not_found"
            )

    async def _validate_create_business_rules(
        self, tenant_id: uuid.UUID, code: str
    ) -> None:
        if await self.repo.get_by_code(tenant_id, code):
            raise ConflictError(
                f"Cohort code '{code}' already exists within tenant '{tenant_id}'.",
                error_code="cohort_code_conflict",
            )

    async def _validate_update_business_rules(
        self, tenant_id: uuid.UUID, cohort_id: uuid.UUID, code: str
    ) -> None:
        existing = await self.repo.get_by_code(tenant_id, code)
        if existing and existing.cohort_id != cohort_id:
            raise ConflictError(
                f"Cohort code '{code}' already exists within tenant '{tenant_id}'.",
                error_code="cohort_code_conflict",
            )

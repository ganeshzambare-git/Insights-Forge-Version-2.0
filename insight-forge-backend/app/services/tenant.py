"""
Insight Forge V2 — Tenant Service.

Orchestrates tenant partition creation, lookup, updates, and validations.
"""

import uuid
from typing import Sequence
from app.models.tenant import Tenant
from app.repositories.tenant import TenantRepository
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import ValidationError, ConflictError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class TenantService(BaseService):
    """Business service governing Tenant lifecycle rules."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the TenantService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = TenantRepository(session=uow.session)

    async def create_tenant(self, slug: str, name: str) -> ServiceResult[Tenant]:
        """Create a new Tenant partition.

        Args:
            slug: Tenant slug identifier.
            name: Institutional name.

        Returns:
            A ServiceResult wrapping the created Tenant entity.
        """
        normalized_slug = slug.strip().lower().replace(" ", "-")

        async def action() -> Tenant:
            self._validate_create_request(normalized_slug, name)
            await self._validate_create_business_rules(normalized_slug)

            tenant = Tenant(
                tenant_id=self.uuid_provider.generate(),
                tenant_slug=normalized_slug,
                tenant_name=name.strip(),
                created_at=self.clock.now(),
            )
            created = await self.repo.create(tenant)
            self.publish_domain_event(
                "TenantCreated",
                {"tenant_id": str(created.tenant_id), "slug": normalized_slug},
            )
            return created

        return await self.execute_command(
            "create_tenant",
            action,
            success_msg=f"Tenant '{name}' created successfully.",
        )

    async def get_tenant(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Fetch a single Tenant by ID.

        Args:
            tenant_id: UUID primary key.

        Returns:
            The Tenant entity if found, otherwise None.
        """
        return await self.repo.get_by_id(tenant_id)

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        """Fetch a single Tenant by URL slug.

        Args:
            slug: URL slug string.

        Returns:
            The Tenant entity if found, otherwise None.
        """
        return await self.repo.get_by_slug(slug.strip().lower())

    async def list_tenants(self, limit: int = 100, offset: int = 0) -> Sequence[Tenant]:
        """List all registered tenants.

        Args:
            limit: Maximum number of records to return.
            offset: Offset skip count.

        Returns:
            A sequence of Tenant entities.
        """
        return await self.repo.get_all(limit=limit, offset=offset)

    async def update_tenant(
        self, tenant_id: uuid.UUID, name: str | None = None, slug: str | None = None
    ) -> ServiceResult[Tenant]:
        """Update Tenant name or slug fields.

        Args:
            tenant_id: Target Tenant UUID.
            name: New institutional name.
            slug: New URL slug.

        Returns:
            A ServiceResult wrapping the updated Tenant entity.
        """

        async def action() -> Tenant:
            tenant = await self.repo.get_by_id(tenant_id)
            if not tenant:
                raise NotFoundError(
                    f"Tenant with ID '{tenant_id}' not found.",
                    error_code="tenant_not_found",
                )

            updates = {}
            if name is not None:
                updates["tenant_name"] = name.strip()
            if slug is not None:
                normalized_slug = slug.strip().lower().replace(" ", "-")
                await self._validate_update_business_rules(tenant_id, normalized_slug)
                updates["tenant_slug"] = normalized_slug

            updated = await self.repo.update(tenant, **updates)
            return updated

        return await self.execute_command(
            "update_tenant",
            action,
            success_msg=f"Tenant '{tenant_id}' updated successfully.",
        )

    async def delete_tenant(self, tenant_id: uuid.UUID) -> ServiceResult[None]:
        """Delete a Tenant partition.

        Args:
            tenant_id: Target Tenant UUID.

        Returns:
            A ServiceResult indicating deletion status.
        """

        async def action() -> None:
            tenant = await self.repo.get_by_id(tenant_id)
            if not tenant:
                raise NotFoundError(
                    f"Tenant with ID '{tenant_id}' not found.",
                    error_code="tenant_not_found",
                )
            await self.repo.delete(tenant)

        return await self.execute_command(
            "delete_tenant",
            action,
            success_msg=f"Tenant '{tenant_id}' deleted successfully.",
        )

    # Private Helpers
    def _validate_create_request(self, slug: str, name: str) -> None:
        if not name.strip():
            raise ValidationError(
                "Tenant name cannot be empty.", error_code="name_required"
            )
        if not slug.strip():
            raise ValidationError(
                "Tenant slug cannot be empty.", error_code="slug_required"
            )

    async def _validate_create_business_rules(self, slug: str) -> None:
        if await self.repo.slug_exists(slug):
            raise ConflictError(
                f"Tenant slug '{slug}' is already taken.", error_code="slug_conflict"
            )

    async def _validate_update_business_rules(
        self, tenant_id: uuid.UUID, slug: str
    ) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.tenant_id != tenant_id:
            raise ConflictError(
                f"Tenant slug '{slug}' is already taken.", error_code="slug_conflict"
            )

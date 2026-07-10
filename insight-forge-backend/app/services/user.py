"""
Insight Forge V2 — User Service.

Orchestrates user accounts creation, lookup, updates, and role validation.
"""

import uuid
from typing import Sequence
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import ValidationError, ConflictError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class UserService(BaseService):
    """Business service governing User account lifecycle rules."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the UserService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = UserRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)
        self.allowed_roles = {"Admin", "Dean", "Faculty", "Student"}

    async def create_user(
        self, tenant_id: uuid.UUID, email: str, password_hash: str, role: str
    ) -> ServiceResult[User]:
        """Create a new user account.

        Args:
            tenant_id: Partner Tenant UUID.
            email: Corporate email address.
            password_hash: Already hashed password.
            role: System role.

        Returns:
            A ServiceResult wrapping the created User entity.
        """
        normalized_email = email.strip().lower()

        async def action() -> User:
            await self._validate_create_request(
                tenant_id, normalized_email, password_hash, role
            )
            await self._validate_create_business_rules(normalized_email)

            user = User(
                user_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                corporate_email=normalized_email,
                password_hash=password_hash,
                assigned_role=role,
                is_mfa_enabled=True,
            )
            created = await self.repo.create(user)
            self.publish_domain_event(
                "UserCreated",
                {"user_id": str(created.user_id), "tenant_id": str(tenant_id)},
            )
            return created

        return await self.execute_command(
            "create_user",
            action,
            success_msg=f"User '{normalized_email}' created successfully.",
        )

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        """Fetch a single User by ID.

        Args:
            user_id: User UUID.

        Returns:
            The User entity if found, otherwise None.
        """
        return await self.repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Fetch a single User by corporate email.

        Args:
            email: Corporate email address.

        Returns:
            The User entity if found, otherwise None.
        """
        return await self.repo.get_by_email(email.strip().lower())

    async def list_users(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[User]:
        """List all users belonging to a tenant (strictly enforces tenant isolation).

        Args:
            tenant_id: Tenant UUID partition scope.
            limit: Maximum number of records to return.
            offset: Offset skip count.

        Returns:
            A sequence of User entities.
        """
        return await self.repo.get_all(tenant_id=tenant_id, limit=limit, offset=offset)

    async def update_user(
        self,
        user_id: uuid.UUID,
        role: str | None = None,
        is_mfa_enabled: bool | None = None,
    ) -> ServiceResult[User]:
        """Update User role or MFA status.

        Args:
            user_id: Target User UUID.
            role: New assigned role.
            is_mfa_enabled: MFA enablement flag.

        Returns:
            A ServiceResult wrapping the updated User entity.
        """

        async def action() -> User:
            user = await self.repo.get_by_id(user_id)
            if not user:
                raise NotFoundError(
                    f"User with ID '{user_id}' not found.", error_code="user_not_found"
                )

            updates = {}
            if role is not None:
                self._validate_role(role)
                updates["assigned_role"] = role
            if is_mfa_enabled is not None:
                updates["is_mfa_enabled"] = is_mfa_enabled

            updated = await self.repo.update(user, **updates)
            return updated

        return await self.execute_command(
            "update_user",
            action,
            success_msg=f"User '{user_id}' updated successfully.",
        )

    async def delete_user(self, user_id: uuid.UUID) -> ServiceResult[None]:
        """Delete a User account.

        Args:
            user_id: Target User UUID.

        Returns:
            A ServiceResult indicating deletion status.
        """

        async def action() -> None:
            user = await self.repo.get_by_id(user_id)
            if not user:
                raise NotFoundError(
                    f"User with ID '{user_id}' not found.", error_code="user_not_found"
                )
            await self.repo.delete(user)

        return await self.execute_command(
            "delete_user",
            action,
            success_msg=f"User '{user_id}' deleted successfully.",
        )

    # Private Helpers
    async def _validate_create_request(
        self, tenant_id: uuid.UUID, email: str, password_hash: str, role: str
    ) -> None:
        if not email.strip():
            raise ValidationError("Email cannot be empty.", error_code="email_required")
        if not password_hash.strip():
            raise ValidationError(
                "Password hash cannot be empty.", error_code="password_required"
            )
        self._validate_role(role)
        # Verify tenant exists
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.", error_code="tenant_not_found"
            )

    def _validate_role(self, role: str) -> None:
        if role not in self.allowed_roles:
            raise ValidationError(
                f"Role '{role}' is invalid. Allowed roles: {self.allowed_roles}",
                error_code="invalid_role",
            )

    async def _validate_create_business_rules(self, email: str) -> None:
        if await self.repo.email_exists(email):
            raise ConflictError(
                f"User email '{email}' is already registered.",
                error_code="email_conflict",
            )

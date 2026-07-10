"""
Insight Forge V2 — Session Service.

Orchestrates user login sessions, JTI validation, and expired session cleanup.
"""

from datetime import datetime
import uuid
from app.models.session import Session
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import ValidationError, ConflictError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class SessionService(BaseService):
    """Business service governing Session authentication rules."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the SessionService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = SessionRepository(session=uow.session)
        self.user_repo = UserRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)

    async def create_session(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        jwt_jti: str,
        expires_at: datetime,
        ingress_ip: str,
    ) -> ServiceResult[Session]:
        """Create a new authenticated login session record.

        Args:
            user_id: Authenticated user UUID.
            tenant_id: User tenant UUID partition.
            jwt_jti: Unique JTI claim.
            expires_at: Time when token expires.
            ingress_ip: Client Ingress IP.

        Returns:
            A ServiceResult wrapping the created Session entity.
        """

        async def action() -> Session:
            await self._validate_create_request(
                user_id, tenant_id, jwt_jti, expires_at, ingress_ip
            )
            await self._validate_create_business_rules(user_id, tenant_id, jwt_jti)

            session_record = Session(
                session_id=self.uuid_provider.generate(),
                user_id=user_id,
                tenant_id=tenant_id,
                jwt_jti=jwt_jti,
                expires_at=expires_at,
                ingress_ip=ingress_ip,
            )
            created = await self.repo.create(session_record)
            self.publish_domain_event(
                "SessionCreated",
                {"session_id": str(created.session_id), "jwt_jti": jwt_jti},
            )
            return created

        return await self.execute_command(
            "create_session",
            action,
            success_msg=f"Session created successfully for user '{user_id}'.",
        )

    async def revoke_session(self, jwt_jti: str) -> ServiceResult[None]:
        """Revoke a session (log out) by its JTI.

        Args:
            jwt_jti: Unique JWT Token JTI identifier.

        Returns:
            A ServiceResult indicating revocation status.
        """

        async def action() -> None:
            session_rec = await self.repo.get_by_jti(jwt_jti)
            if not session_rec:
                raise NotFoundError(
                    f"Session with JTI '{jwt_jti}' not found.",
                    error_code="session_not_found",
                )
            await self.repo.delete(session_rec)
            self.publish_domain_event("SessionRevoked", {"jwt_jti": jwt_jti})

        return await self.execute_command(
            "revoke_session",
            action,
            success_msg=f"Session with JTI '{jwt_jti}' revoked successfully.",
        )

    async def get_session(self, jwt_jti: str) -> Session | None:
        """Fetch a session record by JTI.

        Args:
            jwt_jti: Unique JTI token ID.

        Returns:
            The Session entity if found, otherwise None.
        """
        return await self.repo.get_by_jti(jwt_jti)

    async def cleanup_expired(self, tenant_id: uuid.UUID) -> ServiceResult[int]:
        """Delete all expired sessions belonging to a tenant.

        Args:
            tenant_id: Tenant UUID partition.

        Returns:
            A ServiceResult wrapping the count of cleaned up session records.
        """

        async def action() -> int:
            if not await self.tenant_repo.exists(tenant_id=tenant_id):
                raise NotFoundError(
                    f"Tenant '{tenant_id}' does not exist.",
                    error_code="tenant_not_found",
                )

            now = self.clock.now()
            # Fetch active sessions to audit and delete expired ones (limit 1000 to keep it conservative)
            all_sessions = await self.repo.get_all(tenant_id=tenant_id, limit=1000)
            expired = [s for s in all_sessions if s.expires_at < now]

            for s in expired:
                await self.repo.delete(s)
            return len(expired)

        return await self.execute_command(
            "cleanup_expired",
            action,
            success_msg="Expired sessions cleaned up successfully.",
        )

    # Private Helpers
    async def _validate_create_request(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        jwt_jti: str,
        expires_at: datetime,
        ingress_ip: str,
    ) -> None:
        if not jwt_jti.strip():
            raise ValidationError(
                "JTI token cannot be empty.", error_code="jti_required"
            )
        if not ingress_ip.strip():
            raise ValidationError(
                "Ingress IP cannot be empty.", error_code="ip_required"
            )
        if expires_at <= self.clock.now():
            raise ValidationError(
                "Session expiration must be in the future.", error_code="invalid_expiry"
            )

    async def _validate_create_business_rules(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, jwt_jti: str
    ) -> None:
        # Check tenant exists
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.", error_code="tenant_not_found"
            )

        # Check user exists and belongs to the tenant
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.tenant_id != tenant_id:
            raise ValidationError(
                f"User '{user_id}' does not belong to tenant '{tenant_id}'.",
                error_code="user_tenant_mismatch",
            )

        # Check JTI uniqueness
        if await self.repo.get_by_jti(jwt_jti):
            raise ConflictError(
                f"Session with JTI '{jwt_jti}' already exists.",
                error_code="jti_conflict",
            )

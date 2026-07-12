"""
Insight Forge V2 — Authentication Service.

Orchestrates user logins, token refresh rotation, and logout operations.
"""

from datetime import timedelta, timezone
import time
import uuid
from typing import Any

from app.core.config import settings
from app.core.roles import Role
from app.core.token_types import TokenType
from app.models.session import Session
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.repositories.tenant import TenantRepository
from app.services.base import BaseService
from app.services.result import ServiceResult
from app.services.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider


class AuthService(BaseService):
    """Business service governing Authentication workflows and JTI session validation."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the AuthService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.user_repo = UserRepository(session=uow.session)
        self.session_repo = SessionRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)

    async def signup(
        self, org_name: str, email: str, password: str, client_ip: str
    ) -> ServiceResult[dict[str, Any]]:
        """Register a brand-new organization and its first Admin user, atomically.

        Creates the tenant, the Admin user, and a login session in a single
        transaction, then issues access + refresh tokens so the caller is
        immediately authenticated.

        Args:
            org_name: Institution/organization display name.
            email: Corporate email for the Admin account.
            password: Raw password (already strength-validated at the edge).
            client_ip: Client ingress IP.

        Returns:
            A ServiceResult wrapping the tokens, user, and tenant.
        """
        import re

        from app.core.security import (
            hash_password,
            create_access_token,
            create_refresh_token,
        )

        start_time = time.perf_counter()
        normalized_email = email.strip().lower()
        organization = org_name.strip()

        async def action() -> dict[str, Any]:
            # Reject duplicate accounts up front.
            if await self.user_repo.email_exists(normalized_email):
                raise ConflictError(
                    "An account with this email already exists.",
                    error_code="email_taken",
                )

            # Derive a URL-safe, unique tenant slug from the org name.
            base_slug = re.sub(r"[^a-z0-9]+", "-", organization.lower()).strip("-") or "org"
            slug = base_slug
            if await self.tenant_repo.slug_exists(slug):
                slug = f"{base_slug}-{str(self.uuid_provider.generate())[:8]}"

            tenant = Tenant(
                tenant_id=self.uuid_provider.generate(),
                tenant_slug=slug,
                tenant_name=organization,
                created_at=self.clock.now(),
            )
            await self.tenant_repo.create(tenant)
            # Flush so the tenant row exists before FK-dependent inserts below.
            await self.uow.flush()

            user = User(
                user_id=self.uuid_provider.generate(),
                tenant_id=tenant.tenant_id,
                corporate_email=normalized_email,
                password_hash=hash_password(password),
                assigned_role=Role.ADMIN.value,
                is_mfa_enabled=False,
            )
            await self.user_repo.create(user)
            await self.uow.flush()

            jti = str(self.uuid_provider.generate())
            refresh_expiry = self.clock.now() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            session_record = Session(
                session_id=self.uuid_provider.generate(),
                user_id=user.user_id,
                tenant_id=tenant.tenant_id,
                jwt_jti=jti,
                expires_at=refresh_expiry,
                ingress_ip=client_ip,
            )
            await self.session_repo.create(session_record)

            access_token = create_access_token(
                subject=str(user.user_id),
                tenant_id=str(tenant.tenant_id),
                role=user.assigned_role,
                jti=jti,
            )
            refresh_token = create_refresh_token(
                subject=str(user.user_id),
                tenant_id=str(tenant.tenant_id),
                role=user.assigned_role,
                jti=jti,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            signup_context = ServiceContext(
                tenant_id=tenant.tenant_id,
                user_id=user.user_id,
                role=user.assigned_role,
                request_id=self.context.request_id,
            )
            self.audit_logger.security_event(
                "SIGNUP_SUCCESS",
                signup_context,
                duration_ms=duration_ms,
                detail=f"IP: {client_ip}",
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "user_id": str(user.user_id),
                    "tenant_id": str(tenant.tenant_id),
                    "corporate_email": user.corporate_email,
                    "assigned_role": user.assigned_role,
                },
                "tenant": {
                    "tenant_id": str(tenant.tenant_id),
                    "tenant_slug": tenant.tenant_slug,
                    "tenant_name": tenant.tenant_name,
                },
            }

        return await self.execute_command(
            "signup", action, success_msg="Account created successfully."
        )

    async def login(
        self, email: str, password: str, remember_me: bool, client_ip: str
    ) -> ServiceResult[dict[str, Any]]:
        """Authenticate user credentials and establish a login session.

        Args:
            email: Corporate email address.
            password: Raw password input.
            remember_me: Extend token expiration.
            client_ip: Client Ingress IP.

        Returns:
            A ServiceResult wrapping the tokens and user profile.
        """
        from app.core.security import (
            verify_password,
            create_access_token,
            create_refresh_token,
        )

        start_time = time.perf_counter()
        normalized_email = email.strip().lower()

        async def action() -> dict[str, Any]:
            # Find user
            user = await self.user_repo.get_by_email(normalized_email)
            if not user or not verify_password(password, user.password_hash):
                # Audit Login Failure
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                self.audit_logger.security_event(
                    "LOGIN_FAILED",
                    self.context,
                    duration_ms=duration_ms,
                    detail=f"IP: {client_ip}",
                )
                raise AuthenticationError(
                    "Invalid email or password.", error_code="invalid_credentials"
                )

            # future hook: if user.is_mfa_enabled: ...

            # Generate new JTI session ID
            jti = str(self.uuid_provider.generate())

            # Configure expiration
            refresh_days = 30 if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
            refresh_expiry = self.clock.now() + timedelta(days=refresh_days)

            # Save JTI session to DB
            session_record = Session(
                session_id=self.uuid_provider.generate(),
                user_id=user.user_id,
                tenant_id=user.tenant_id,
                jwt_jti=jti,
                expires_at=refresh_expiry,
                ingress_ip=client_ip,
            )
            await self.session_repo.create(session_record)

            # Encode tokens
            access_token = create_access_token(
                subject=str(user.user_id),
                tenant_id=str(user.tenant_id),
                role=user.assigned_role,
                jti=jti,
            )
            refresh_token = create_refresh_token(
                subject=str(user.user_id),
                tenant_id=str(user.tenant_id),
                role=user.assigned_role,
                jti=jti,
                expires_delta=timedelta(days=refresh_days),
            )

            # Audit Success
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            login_context = ServiceContext(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                role=user.assigned_role,
                request_id=self.context.request_id,
            )
            self.audit_logger.security_event(
                "LOGIN_SUCCESS",
                login_context,
                duration_ms=duration_ms,
                detail=f"IP: {client_ip}",
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "user_id": str(user.user_id),
                    "tenant_id": str(user.tenant_id),
                    "corporate_email": user.corporate_email,
                    "assigned_role": user.assigned_role,
                },
            }

        return await self.execute_command("login", action)

    async def refresh_token(
        self, refresh_token_str: str, client_ip: str
    ) -> ServiceResult[dict[str, Any]]:
        """Rotate JWT tokens and invalidate the old session.

        Args:
            refresh_token_str: Serialized Refresh Token string.
            client_ip: Client Ingress IP.

        Returns:
            A ServiceResult wrapping the rotated tokens.
        """
        from app.core.security import (
            decode_token,
            create_access_token,
            create_refresh_token,
        )

        start_time = time.perf_counter()

        async def action() -> dict[str, Any]:
            # Decode token
            payload = decode_token(refresh_token_str)
            token_type = payload.get("type")
            if token_type != TokenType.REFRESH.value:
                raise AuthenticationError(
                    "Invalid token type.", error_code="invalid_token_type"
                )

            jti = payload.get("jti")
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            role = payload.get("role")

            if not jti or not user_id:
                raise AuthenticationError(
                    "Invalid token payload claims.", error_code="invalid_claims"
                )

            user_uuid = uuid.UUID(user_id)
            tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

            # Look up session
            session_record = await self.session_repo.get_by_jti(jti)

            # Token Reuse Attack Detection
            if not session_record:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                attack_context = ServiceContext(
                    tenant_id=tenant_uuid,
                    user_id=user_uuid,
                    role=role,
                    request_id=self.context.request_id,
                )
                self.audit_logger.security_event(
                    "TOKEN_REUSE_DETECTED",
                    attack_context,
                    duration_ms=duration_ms,
                    detail=f"Reused JTI: {jti} | IP: {client_ip}",
                )
                raise AuthenticationError(
                    "Reused or revoked token detected.", error_code="token_reused"
                )

            # Delete old session (rotation)
            await self.session_repo.delete(session_record)

            # Validate expiration
            if (
                session_record.expires_at.replace(tzinfo=timezone.utc)
                < self.clock.now()
            ):
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                self.audit_logger.security_event(
                    "TOKEN_REVOKED",
                    self.context,
                    duration_ms=duration_ms,
                    detail=f"Expired JTI: {jti}",
                )
                raise AuthenticationError(
                    "Session has expired.", error_code="session_expired"
                )

            # Create new session with rotated JTI
            new_jti = str(self.uuid_provider.generate())
            new_refresh_expiry = self.clock.now() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            new_session = Session(
                session_id=self.uuid_provider.generate(),
                user_id=user_uuid,
                tenant_id=tenant_uuid,
                jwt_jti=new_jti,
                expires_at=new_refresh_expiry,
                ingress_ip=client_ip,
            )
            await self.session_repo.create(new_session)

            # Generate new tokens
            new_access = create_access_token(
                subject=user_id,
                tenant_id=tenant_id,
                role=role,
                jti=new_jti,
            )
            new_refresh = create_refresh_token(
                subject=user_id,
                tenant_id=tenant_id,
                role=role,
                jti=new_jti,
            )

            # Audit Token Refresh
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            refresh_context = ServiceContext(
                tenant_id=tenant_uuid,
                user_id=user_uuid,
                role=role,
                request_id=self.context.request_id,
            )
            self.audit_logger.security_event(
                "TOKEN_REFRESH",
                refresh_context,
                duration_ms=duration_ms,
                detail=f"IP: {client_ip}",
            )

            return {
                "access_token": new_access,
                "refresh_token": new_refresh,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

        return await self.execute_command("refresh_token", action)

    async def logout(self, jwt_jti: str) -> ServiceResult[None]:
        """Revoke a user login session by its JTI.

        Args:
            jwt_jti: Target JTI session ID.

        Returns:
            A ServiceResult indicating completion status.
        """

        async def action() -> None:
            session_record = await self.session_repo.get_by_jti(jwt_jti)
            if not session_record:
                raise NotFoundError(
                    f"Session with JTI '{jwt_jti}' not found.",
                    error_code="session_not_found",
                )
            await self.session_repo.delete(session_record)

            self.audit_logger.security_event("LOGOUT", self.context)

        return await self.execute_command(
            "logout", action, success_msg="Logged out successfully."
        )

    async def logout_all(self, user_id: uuid.UUID) -> ServiceResult[None]:
        """Revoke all login sessions belonging to a specific user.

        Args:
            user_id: User UUID.

        Returns:
            A ServiceResult indicating completion status.
        """

        async def action() -> None:
            # Query all sessions matching user_id. SessionRepository.get_all does not take user_id
            # directly in signature, but supports extra filter keyword args through BaseRepository get_all.
            sessions = await self.session_repo.get_all(user_id=user_id, limit=500)
            for s in sessions:
                await self.session_repo.delete(s)

            self.audit_logger.security_event("LOGOUT_ALL", self.context)

        return await self.execute_command(
            "logout_all",
            action,
            success_msg="Logged out of all sessions successfully.",
        )

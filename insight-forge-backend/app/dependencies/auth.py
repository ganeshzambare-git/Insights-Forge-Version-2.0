"""
Insight Forge V2 — Route Authentication & Authorization Guards.

Defines FastAPI dependencies for verifying JWT scopes, active DB sessions, and RBAC constraints.
"""

from datetime import datetime, timezone
import uuid
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import decode_token
from app.core.token_types import TokenType
from app.core.roles import Role
from app.models.user import User
from app.models.session import Session as UserSession
from app.repositories.user import UserRepository
from app.repositories.session import SessionRepository
from app.services.exceptions import AuthenticationError, AuthorizationError

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> UserSession:
    """FastAPI dependency to extract and validate the active login session.

    Args:
        credentials: Bearer Authorization token payload.
        db: Database AsyncSession.

    Returns:
        The validated database Session record.

    Raises:
        AuthenticationError: If token signature, expiry, type or JTI check fails.
    """
    if not credentials:
        raise AuthenticationError(
            "Authorization credentials missing.", error_code="auth_missing"
        )
    token = credentials.credentials

    # Decode and validate claims (signatures, issuer, audience, and exp)
    payload = decode_token(token)

    token_type = payload.get("type")
    if token_type != TokenType.ACCESS.value:
        raise AuthenticationError(
            "Invalid token type.", error_code="invalid_token_type"
        )

    jti = payload.get("jti")
    if not jti:
        raise AuthenticationError("Invalid token identifier.", error_code="invalid_jti")

    session_repo = SessionRepository(db)
    session_record = await session_repo.get_by_jti(jti)
    if not session_record:
        raise AuthenticationError(
            "Active session not found or has been revoked.",
            error_code="session_revoked",
        )

    # Validate db session expiration
    if session_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
        timezone.utc
    ):
        await session_repo.delete(session_record)
        raise AuthenticationError("Session has expired.", error_code="session_expired")

    return session_record


async def get_current_user(
    session_record: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """FastAPI dependency to load the active User record.

    Args:
        session_record: Active verified Session record.
        db: Database AsyncSession.

    Returns:
        The User database entity.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(session_record.user_id)
    if not user:
        raise AuthenticationError(
            "Authenticated user record not found.", error_code="user_not_found"
        )
    return user


def get_current_tenant(
    session_record: UserSession = Depends(get_current_session),
) -> uuid.UUID:
    """FastAPI dependency to fetch the tenant ID of the authenticated user session.

    Args:
        session_record: Active verified Session record.

    Returns:
        The Tenant UUID.
    """
    return session_record.tenant_id


class RequireRoles:
    """Declarative dependency check to enforce Role-Based Access Control (RBAC)."""

    def __init__(self, *allowed_roles: Role) -> None:
        """Initialize the guard with allowed Role members.

        Args:
            allowed_roles: Role enum arguments.
        """
        self.allowed_roles = {role.value for role in allowed_roles}

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """Verify the user role.

        Args:
            current_user: Loaded active User record.

        Returns:
            The verified User record.

        Raises:
            AuthorizationError: If the role claim is not authorized.
        """
        if current_user.assigned_role not in self.allowed_roles:
            raise AuthorizationError(
                f"Access denied. Required roles: {self.allowed_roles}",
                error_code="role_forbidden",
            )
        return current_user

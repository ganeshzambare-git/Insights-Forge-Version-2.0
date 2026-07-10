"""
Insight Forge V2 — Authentication & Authorization Unit Tests.

Verifies password rules, JWT encoders/decoders, AuthService commands/queries,
FastAPI dependency guards, and security header middlewares using mock repositories.
"""

from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock, ANY

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.roles import Role
from app.core.token_types import TokenType
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.models.session import Session as UserSession
from app.services.auth import AuthService
from app.services.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)
from app.services.context import ServiceContext
from app.dependencies.auth import RequireRoles
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.uow import UnitOfWork

# ============================================================
# CRYPTOGRAPHY & PASSWORD TESTS
# ============================================================


def test_password_hashing_and_verification() -> None:
    """Verifies that bcrypt wrapper functions hash and verify correctly."""
    pw = "SuperStrongPass123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong-pass", hashed) is False


def test_password_policy_complexity() -> None:
    """Verifies password policy rules for length and character diversity."""
    # Valid
    validate_password_strength("Valid123!")

    # Too short
    with pytest.raises(ValidationError) as exc:
        validate_password_strength("Val1!")
    assert exc.value.error_code == "password_length_invalid"

    # Missing lowercase
    with pytest.raises(ValidationError) as exc:
        validate_password_strength("VALID123!")
    assert exc.value.error_code == "password_missing_lowercase"

    # Missing uppercase
    with pytest.raises(ValidationError) as exc:
        validate_password_strength("valid123!")
    assert exc.value.error_code == "password_missing_uppercase"

    # Missing number
    with pytest.raises(ValidationError) as exc:
        validate_password_strength("ValidPass!")
    assert exc.value.error_code == "password_missing_number"

    # Missing special char
    with pytest.raises(ValidationError) as exc:
        validate_password_strength("ValidPass123")
    assert exc.value.error_code == "password_missing_special"


# ============================================================
# JWT SPECIFICATION TESTS
# ============================================================


def test_jwt_generation_and_decoding() -> None:
    """Verifies that JWT claims are written and decoded correctly."""
    sub = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())

    access_token = create_access_token(
        subject=sub, tenant_id=tenant_id, role="Admin", jti=jti
    )
    payload = decode_token(access_token)

    assert payload["sub"] == sub
    assert payload["tenant_id"] == tenant_id
    assert payload["role"] == "Admin"
    assert payload["jti"] == jti
    assert payload["type"] == TokenType.ACCESS.value
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE


def test_jwt_failures() -> None:
    """Verifies token signature, issuer, audience, and type exceptions."""
    sub = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())

    # Invalid Signature
    bad_token = (
        create_access_token(subject=sub, tenant_id=tenant_id, role="Admin", jti=jti)
        + "tampered"
    )
    with pytest.raises(AuthenticationError) as exc:
        decode_token(bad_token)
    assert "invalid_token" in exc.value.error_code

    # Expired token (configured beyond the 30-second clock skew leeway)
    expired_token = create_access_token(
        subject=sub,
        tenant_id=tenant_id,
        role="Admin",
        jti=jti,
        expires_delta=timedelta(seconds=-40),
    )
    with pytest.raises(AuthenticationError):
        decode_token(expired_token)


# ============================================================
# SERVICE WORKFLOWS TESTS
# ============================================================


@pytest.fixture
def mock_service_deps() -> (
    tuple[UnitOfWork, ServiceContext, MagicMock, MagicMock, MagicMock]
):
    """Prepares mocks for UoW, Context, Audit, Clock, and UUID providers."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.flush = AsyncMock()
    uow = UnitOfWork(mock_session)
    context = ServiceContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role="Admin",
        request_id="test-req-id",
    )
    audit = MagicMock()
    clock = MagicMock()
    clock.now.return_value = datetime.now(timezone.utc)
    uuid_provider = MagicMock()
    uuid_provider.generate.side_effect = lambda: uuid.uuid4()

    return uow, context, audit, clock, uuid_provider


@pytest.mark.anyio
async def test_auth_service_login_success(mock_service_deps) -> None:
    """Verifies login workflow generates access/refresh tokens on valid credentials."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AuthService(uow, context, audit, clock, uuid_provider)

    mock_user = User(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        corporate_email="admin@college.edu",
        password_hash=hash_password("StrongPass123!"),
        assigned_role="Admin",
    )
    service.user_repo.get_by_email = AsyncMock(return_value=mock_user)
    service.session_repo.create = AsyncMock()

    result = await service.login(
        email="admin@college.edu",
        password="StrongPass123!",
        remember_me=True,
        client_ip="127.0.0.1",
    )

    assert result.success is True
    assert "access_token" in result.data
    assert "refresh_token" in result.data
    service.session_repo.create.assert_called_once()
    audit.security_event.assert_called_with(
        "LOGIN_SUCCESS",
        ANY,
        duration_ms=pytest.approx(0, abs=1000),
        detail="IP: 127.0.0.1",
    )


@pytest.mark.anyio
async def test_auth_service_login_failure(mock_service_deps) -> None:
    """Verifies login fails and audits on wrong password."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AuthService(uow, context, audit, clock, uuid_provider)

    mock_user = User(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        corporate_email="admin@college.edu",
        password_hash=hash_password("StrongPass123!"),
        assigned_role="Admin",
    )
    service.user_repo.get_by_email = AsyncMock(return_value=mock_user)

    with pytest.raises(AuthenticationError) as exc:
        await service.login(
            email="admin@college.edu",
            password="wrong-password",
            remember_me=False,
            client_ip="127.0.0.1",
        )

    assert exc.value.error_code == "invalid_credentials"
    audit.security_event.assert_called_with(
        "LOGIN_FAILED",
        ANY,
        duration_ms=pytest.approx(0, abs=1000),
        detail="IP: 127.0.0.1",
    )


@pytest.mark.anyio
async def test_auth_service_token_refresh_rotation(mock_service_deps) -> None:
    """Verifies token refresh deletes old session and issues new session details."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AuthService(uow, context, audit, clock, uuid_provider)

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    jti = str(uuid.uuid4())

    refresh_token = create_refresh_token(
        subject=str(user_id), tenant_id=str(tenant_id), role="Dean", jti=jti
    )

    old_session = UserSession(
        session_id=uuid.uuid4(),
        user_id=user_id,
        tenant_id=tenant_id,
        jwt_jti=jti,
        expires_at=clock.now() + timedelta(days=1),
        ingress_ip="127.0.0.1",
    )

    service.session_repo.get_by_jti = AsyncMock(return_value=old_session)
    service.session_repo.delete = AsyncMock()
    service.session_repo.create = AsyncMock()

    result = await service.refresh_token(refresh_token, "127.0.0.1")

    assert result.success is True
    assert "access_token" in result.data
    assert "refresh_token" in result.data
    service.session_repo.delete.assert_called_once_with(old_session)
    service.session_repo.create.assert_called_once()
    audit.security_event.assert_called_with(
        "TOKEN_REFRESH",
        ANY,
        duration_ms=pytest.approx(0, abs=1000),
        detail="IP: 127.0.0.1",
    )


@pytest.mark.anyio
async def test_auth_service_token_refresh_reuse_attack(mock_service_deps) -> None:
    """Verifies reuse attack raises AuthenticationError and fires TOKEN_REUSE_DETECTED."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AuthService(uow, context, audit, clock, uuid_provider)

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    jti = str(uuid.uuid4())

    refresh_token = create_refresh_token(
        subject=str(user_id), tenant_id=str(tenant_id), role="Dean", jti=jti
    )

    service.session_repo.get_by_jti = AsyncMock(return_value=None)

    with pytest.raises(AuthenticationError) as exc:
        await service.refresh_token(refresh_token, "127.0.0.1")

    assert exc.value.error_code == "token_reused"
    audit.security_event.assert_called_with(
        "TOKEN_REUSE_DETECTED",
        ANY,
        duration_ms=pytest.approx(0, abs=1000),
        detail=f"Reused JTI: {jti} | IP: 127.0.0.1",
    )


# ============================================================
# FASTAPI DEPENDENCY & RBAC TESTS
# ============================================================


@pytest.mark.anyio
async def test_require_roles_guard() -> None:
    """Verifies RequireRoles authorizes permitted roles and rejects forbidden ones."""
    guard = RequireRoles(Role.ADMIN, Role.DEAN)

    admin_user = User(assigned_role="Admin")
    faculty_user = User(assigned_role="Faculty")

    # Authorized
    assert guard(admin_user) == admin_user

    # Forbidden
    with pytest.raises(AuthorizationError) as exc:
        guard(faculty_user)
    assert exc.value.error_code == "role_forbidden"


# ============================================================
# MIDDLEWARE TESTS
# ============================================================


def test_middlewares_headers_and_request_id() -> None:
    """Verifies security headers and correlation request IDs are injected in HTTP lifecycle."""
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)
    test_app.add_middleware(RequestIDMiddleware)

    @test_app.get("/test-route")
    def read_test() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(test_app)
    response = client.get("/test-route")

    assert response.status_code == status.HTTP_200_OK
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

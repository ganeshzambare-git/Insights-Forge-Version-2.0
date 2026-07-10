"""
Insight Forge V2 — JWT Security.

Handles encoding, decoding, and claim validations for JWT access and refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError

from app.core.config import settings
from app.core.token_types import TokenType


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    jti: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode an access token with claims metadata.

    Args:
        subject: User ID string.
        tenant_id: Tenant UUID string.
        role: User role string.
        jti: Unique session token ID.
        expires_delta: Optional custom duration.

    Returns:
        The serialized JWT token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "jti": jti,
        "type": TokenType.ACCESS.value,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    # Future hook for RS256: load private key from path and call jwt.encode with RS256 algorithm
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    tenant_id: str,
    role: str,
    jti: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a refresh token with claims metadata.

    Args:
        subject: User ID string.
        tenant_id: Tenant UUID string.
        role: User role string.
        jti: Unique session token ID.
        expires_delta: Optional custom duration.

    Returns:
        The serialized JWT token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    claims = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "jti": jti,
        "type": TokenType.REFRESH.value,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate claims of a JWT.

    Args:
        token: Raw serialized token.

    Returns:
        The decoded claims payload dict.

    Raises:
        AuthenticationError: If decoding fails or signature is invalid.
    """
    from app.services.exceptions import AuthenticationError
    try:
        # Future hook for RS256: load public key from path and call jwt.decode
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={"leeway": 30},
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(
            f"Invalid or expired credentials: {str(e)}",
            error_code="invalid_token",
        )

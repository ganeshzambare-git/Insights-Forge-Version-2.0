"""
Insight Forge V2 — Authentication Controller Routes.

Exposes endpoints for user login, token refresh rotation, and logout operations.
"""

from typing import Any
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.core.security import validate_password_strength
from app.models.user import User
from app.models.session import Session as UserSession
from app.dependencies.auth import get_current_user, get_current_session
from app.dependencies.services import get_auth_service
from app.services.auth import AuthService
from app.utils.response import api_response

router = APIRouter(prefix="/auth", tags=["auth"])


# Request / Response Schemas
class LoginRequest(BaseModel):
    """Schema representing user login credentials."""

    corporate_email: EmailStr = Field(
        ..., json_schema_extra={"example": "admin@college.edu"}
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        json_schema_extra={"example": "StrongPass123!"},
    )
    remember_me: bool = Field(default=False, json_schema_extra={"example": False})


class SignupRequest(BaseModel):
    """Schema representing new-organization signup details."""

    organization_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        json_schema_extra={"example": "Springfield College"},
    )
    corporate_email: EmailStr = Field(
        ..., json_schema_extra={"example": "admin@springfield.edu"}
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        json_schema_extra={"example": "StrongPass123!"},
    )


class RefreshRequest(BaseModel):
    """Schema representing JWT token rotation criteria."""

    refresh_token: str = Field(
        ..., json_schema_extra={"example": "eyJhbGciOiJIUzI1Ni..."}
    )


# Controller routes
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    payload: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Register a new organization and its first Admin user, returning tokens.

    Enforces password complexity before creating the tenant + Admin account.
    """
    validate_password_strength(payload.password)

    client_ip = request.client.host if request.client else "127.0.0.1"

    result = await auth_service.signup(
        org_name=payload.organization_name,
        email=payload.corporate_email,
        password=payload.password,
        client_ip=client_ip,
    )
    return api_response(
        success=True,
        message=result.message or "Account created successfully",
        data=result.data,
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Authenticate user credentials and create a session.

    Enforces password complexity policies before running authorization rules.
    """
    # Enforce password policy strength
    validate_password_strength(payload.password)

    client_ip = request.client.host if request.client else "127.0.0.1"

    result = await auth_service.login(
        email=payload.corporate_email,
        password=payload.password,
        remember_me=payload.remember_me,
        client_ip=client_ip,
    )
    return api_response(
        success=True, message=result.message or "Login successful", data=result.data
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    payload: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Rotate JWT access and refresh tokens, invalidating the previous session JTI."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    result = await auth_service.refresh_token(
        refresh_token_str=payload.refresh_token, client_ip=client_ip
    )
    return api_response(
        success=True,
        message=result.message or "Token refreshed successfully",
        data=result.data,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    session: UserSession = Depends(get_current_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Invalidate the current user login session JTI."""
    result = await auth_service.logout(jwt_jti=session.jwt_jti)
    return api_response(success=True, message=result.message or "Logged out")


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Invalidate all active login sessions belonging to the user."""
    result = await auth_service.logout_all(user_id=current_user.user_id)
    return api_response(
        success=True, message=result.message or "Logged out of all sessions"
    )


@router.get("/me", status_code=status.HTTP_200_OK)
async def me(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Fetch the profile details of the currently authenticated user."""
    user_data = {
        "user_id": str(current_user.user_id),
        "tenant_id": str(current_user.tenant_id),
        "corporate_email": current_user.corporate_email,
        "assigned_role": current_user.assigned_role,
        "is_mfa_enabled": current_user.is_mfa_enabled,
    }
    return api_response(
        success=True, message="Profile fetched successfully", data=user_data
    )

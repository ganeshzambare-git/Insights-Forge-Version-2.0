"""
Insight Forge V2 — Users Router.

Exposes REST CRUD endpoints governing User profiles, with strict tenant isolation.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.core.security import hash_password
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_user_service
from app.models.user import User
from app.services.user import UserService
from app.api.v1.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.response import api_response
from app.services.exceptions import NotFoundError, AuthorizationError

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Create User",
    description="Register a new user account. Requires Admin or Dean privileges.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def create_user(
    request: Request,
    payload: UserCreate,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Target tenant UUID partition (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Enforce tenant isolation for Deans
    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    # Decouple password hashing
    pw_hash = hash_password(payload.password)

    result = await service.create_user(
        tenant_id=target_tenant_id,
        email=payload.corporate_email,
        password_hash=pw_hash,
        role=payload.assigned_role.value,
    )

    data = UserResponse.model_validate(result.data).model_dump()
    return api_response(
        success=True,
        message=result.message or "User created successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get User",
    description="Retrieve user profile by UUID. Enforces tenant isolation.",
)
async def get_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    user = await service.get_user(user_id)
    if not user:
        raise NotFoundError(
            f"User with ID '{user_id}' not found.", error_code="user_not_found"
        )

    # Tenant isolation and self-access check
    if current_user.assigned_role != Role.ADMIN.value:
        if user.tenant_id != current_user.tenant_id:
            raise AuthorizationError(
                "Access denied to target tenant partition.",
                error_code="tenant_forbidden",
            )
        if (
            current_user.assigned_role not in (Role.DEAN.value, Role.FACULTY.value)
            and current_user.user_id != user_id
        ):
            raise AuthorizationError(
                "Access denied to this profile.", error_code="role_forbidden"
            )

    data = UserResponse.model_validate(user).model_dump()
    return api_response(
        success=True,
        message="User profile retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Update User",
    description="Partially update user role or MFA flags. Requires Admin or Dean.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Fetch user to verify tenant isolation
    user = await service.get_user(user_id)
    if not user:
        raise NotFoundError(
            f"User with ID '{user_id}' not found.", error_code="user_not_found"
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and user.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    role_val = payload.assigned_role.value if payload.assigned_role else None
    result = await service.update_user(
        user_id=user_id, role=role_val, is_mfa_enabled=payload.is_mfa_enabled
    )

    data = UserResponse.model_validate(result.data).model_dump()
    return api_response(
        success=True,
        message=result.message or "User updated successfully.",
        data=data,
        request_id=req_id,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Remove user account. Requires Admin or Dean.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> None:
    # Fetch user to verify tenant isolation
    user = await service.get_user(user_id)
    if not user:
        raise NotFoundError(
            f"User with ID '{user_id}' not found.", error_code="user_not_found"
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and user.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    await service.delete_user(user_id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Users",
    description="List users under active tenant scope. Admin can filter across all tenants.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def list_users(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Filter by tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Enforce tenant isolation
    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    users = await service.list_users(
        tenant_id=target_tenant_id, limit=limit, offset=offset
    )

    data = [UserResponse.model_validate(u).model_dump() for u in users]
    meta = {
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(data),
        }
    }
    return api_response(
        success=True,
        message="Users listed successfully.",
        data=data,
        meta=meta,
        request_id=req_id,
    )


# ============================================================
# FUTURE BULK OPERATIONS HOOKS (DOCUMENTATION & COMMENTS ONLY)
# ============================================================
# TODO: Future bulk import of user accounts:
# POST /users/bulk
#   - payload: UserBulkImportRequest
#   - role: Admin / Dean only
#   - execution: FastAPI BackgroundTasks or asyncio batch processing

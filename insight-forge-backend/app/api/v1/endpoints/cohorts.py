"""
Insight Forge V2 — Cohorts Router.

Exposes REST CRUD endpoints governing Cohorts, scoped by active tenant partition.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_cohort_service
from app.models.user import User
from app.services.cohort import CohortService
from app.api.v1.schemas.cohort import CohortCreate, CohortUpdate, CohortResponse
from app.utils.response import api_response
from app.services.exceptions import NotFoundError, AuthorizationError

router = APIRouter(
    prefix="/cohorts",
    tags=["cohorts"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Create Cohort",
    description="Establish a new student cohort within the tenant partition.",
)
async def create_cohort(
    request: Request,
    payload: CohortCreate,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: CohortService = Depends(get_cohort_service),
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

    result = await service.create_cohort(
        tenant_id=target_tenant_id,
        cohort_code=payload.cohort_code,
        department_scope=payload.department_scope,
    )

    data = CohortResponse.model_validate(result.data).model_dump()
    return api_response(
        success=True,
        message=result.message or "Cohort created successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/{cohort_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Cohort",
    description="Retrieve cohort details by UUID. Enforces tenant boundaries.",
)
async def get_cohort(
    request: Request,
    cohort_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CohortService = Depends(get_cohort_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    cohort = await service.get_cohort(cohort_id)
    if not cohort:
        raise NotFoundError(
            f"Cohort with ID '{cohort_id}' not found.",
            error_code="cohort_not_found",
        )

    # Tenant isolation check
    if (
        current_user.assigned_role != Role.ADMIN.value
        and cohort.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    data = CohortResponse.model_validate(cohort).model_dump()
    return api_response(
        success=True,
        message="Cohort retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.patch(
    "/{cohort_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Update Cohort",
    description="Partially update cohort properties. Enforces tenant boundaries.",
)
async def update_cohort(
    request: Request,
    cohort_id: uuid.UUID,
    payload: CohortUpdate,
    current_user: User = Depends(get_current_user),
    service: CohortService = Depends(get_cohort_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Fetch cohort first to verify isolation
    cohort = await service.get_cohort(cohort_id)
    if not cohort:
        raise NotFoundError(
            f"Cohort with ID '{cohort_id}' not found.",
            error_code="cohort_not_found",
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and cohort.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    result = await service.update_cohort(
        cohort_id=cohort_id,
        cohort_code=payload.cohort_code,
        department_scope=payload.department_scope,
    )

    data = CohortResponse.model_validate(result.data).model_dump()
    return api_response(
        success=True,
        message=result.message or "Cohort updated successfully.",
        data=data,
        request_id=req_id,
    )


@router.delete(
    "/{cohort_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Cohort",
    description="Remove cohort partition scope.",
)
async def delete_cohort(
    cohort_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CohortService = Depends(get_cohort_service),
) -> None:
    # Fetch cohort first to verify isolation
    cohort = await service.get_cohort(cohort_id)
    if not cohort:
        raise NotFoundError(
            f"Cohort with ID '{cohort_id}' not found.",
            error_code="cohort_not_found",
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and cohort.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    await service.repo.delete(cohort)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Cohorts",
    description="List cohorts under active tenant partition.",
)
async def list_cohorts(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: CohortService = Depends(get_cohort_service),
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

    cohorts = await service.list_cohorts(
        tenant_id=target_tenant_id, limit=limit, offset=offset
    )

    data = [CohortResponse.model_validate(c).model_dump() for c in cohorts]
    meta = {
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(data),
        }
    }
    return api_response(
        success=True,
        message="Cohorts listed successfully.",
        data=data,
        meta=meta,
        request_id=req_id,
    )

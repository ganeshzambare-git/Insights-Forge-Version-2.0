"""
Insight Forge V2 — Datasets Router.

Exposes REST endpoints for registering and tracking uploaded datasets,
scoped by the active tenant partition. This layer only manages dataset
metadata and lifecycle status — it never parses or cleans the raw file.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.v1.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetStatusUpdate,
)
from app.core.roles import Role
from app.dependencies.auth import RequireRoles, get_current_user
from app.dependencies.services import get_dataset_service
from app.models.user import User
from app.services.dataset import DatasetService
from app.services.exceptions import AuthorizationError, NotFoundError
from app.utils.response import api_response

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


def _resolve_target_tenant(
    current_user: User, tenant_id: uuid.UUID | None
) -> uuid.UUID:
    """Resolve the tenant scope, allowing Admins to target another tenant.

    Args:
        current_user: The authenticated user.
        tenant_id: Optional tenant override supplied via query parameter.

    Returns:
        The tenant UUID the operation should run against.

    Raises:
        AuthorizationError: If a non-Admin attempts to target another tenant.
    """
    if current_user.assigned_role == Role.ADMIN.value:
        return tenant_id or current_user.tenant_id
    if tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )
    return current_user.tenant_id


def _assert_tenant_access(current_user: User, resource_tenant_id: uuid.UUID) -> None:
    """Ensure a non-Admin user may only touch resources in their own tenant."""
    if (
        current_user.assigned_role != Role.ADMIN.value
        and resource_tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Register Dataset",
    description="Register a new dataset record in the Pending state. Admin only.",
)
async def register_dataset(
    request: Request,
    payload: DatasetCreate,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
    _admin: None = Depends(RequireRoles(Role.ADMIN)),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = _resolve_target_tenant(current_user, tenant_id)

    result = await service.register_dataset(
        tenant_id=target_tenant_id,
        original_filename=payload.original_filename,
        source_format=payload.source_format,
        size_bytes=payload.size_bytes,
    )

    data = DatasetResponse.model_validate(result.data).model_dump(mode="json")
    return api_response(
        success=True,
        message=result.message or "Dataset registered successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Datasets",
    description="List datasets under the active tenant partition, newest first.",
)
async def list_datasets(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = _resolve_target_tenant(current_user, tenant_id)

    datasets = await service.list_datasets(
        tenant_id=target_tenant_id, limit=limit, offset=offset
    )

    data = [
        DatasetResponse.model_validate(d).model_dump(mode="json") for d in datasets
    ]
    meta = {
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(data),
        }
    }
    return api_response(
        success=True,
        message="Datasets listed successfully.",
        data=data,
        meta=meta,
        request_id=req_id,
    )


@router.get(
    "/{dataset_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Dataset",
    description="Retrieve a dataset (status + health score) by UUID. Enforces tenant boundaries.",
)
async def get_dataset(
    request: Request,
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError(
            f"Dataset with ID '{dataset_id}' not found.",
            error_code="dataset_not_found",
        )

    _assert_tenant_access(current_user, dataset.tenant_id)

    data = DatasetResponse.model_validate(dataset).model_dump(mode="json")
    return api_response(
        success=True,
        message="Dataset retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.patch(
    "/{dataset_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Update Dataset Status",
    description="Update a dataset's processing status and health metrics. Admin only.",
)
async def update_dataset_status(
    request: Request,
    dataset_id: uuid.UUID,
    payload: DatasetStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
    _admin: None = Depends(RequireRoles(Role.ADMIN)),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError(
            f"Dataset with ID '{dataset_id}' not found.",
            error_code="dataset_not_found",
        )

    _assert_tenant_access(current_user, dataset.tenant_id)

    result = await service.update_status(
        dataset_id=dataset_id,
        processing_status=payload.processing_status,
        health_score=payload.health_score,
        row_count=payload.row_count,
    )

    data = DatasetResponse.model_validate(result.data).model_dump(mode="json")
    return api_response(
        success=True,
        message=result.message or "Dataset updated successfully.",
        data=data,
        request_id=req_id,
    )


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Dataset",
    description="Remove a dataset record. Admin only.",
)
async def delete_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
    _admin: None = Depends(RequireRoles(Role.ADMIN)),
):
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError(
            f"Dataset with ID '{dataset_id}' not found.",
            error_code="dataset_not_found",
        )

    _assert_tenant_access(current_user, dataset.tenant_id)

    await service.delete_dataset(dataset_id)

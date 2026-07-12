"""
Insight Forge V2 — Datasets Router.

Lists stored datasets, returns a single dataset's status/health, and paginates
its stored rows. All queries are tenant-scoped.
"""

from typing import Any
import uuid

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_dataset_service
from app.models.user import User
from app.services.dataset import DatasetService
from app.api.v1.schemas.dataset import DatasetRecordResponse, DatasetResponse
from app.utils.response import api_response

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Datasets",
    description="List datasets stored for the active tenant, newest first.",
)
async def list_datasets(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    datasets = await service.list_datasets(
        current_user.tenant_id, limit=limit, offset=offset
    )
    data = [DatasetResponse.model_validate(d).model_dump() for d in datasets]
    return api_response(
        success=True,
        message="Datasets retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/{dataset_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Dataset",
    description="Return a single dataset's metadata, status, and health score.",
)
async def get_dataset(
    request: Request,
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    dataset = await service.get_dataset(current_user.tenant_id, dataset_id)
    return api_response(
        success=True,
        message="Dataset retrieved successfully.",
        data=DatasetResponse.model_validate(dataset).model_dump(),
        request_id=req_id,
    )


@router.get(
    "/{dataset_id}/records",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Dataset Records",
    description="Paginate the stored rows of a dataset in original order.",
)
async def list_dataset_records(
    request: Request,
    dataset_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    records = await service.get_records(
        current_user.tenant_id, dataset_id, limit=limit, offset=offset
    )
    data = [DatasetRecordResponse.model_validate(r).model_dump() for r in records]
    return api_response(
        success=True,
        message="Dataset records retrieved successfully.",
        data=data,
        request_id=req_id,
    )

"""
Insight Forge V2 — Ingestion Router.

Receives raw dataset uploads, streams them into storage, registers a dataset
record, and hands off to the cleaning worker. This layer stores the file only;
it never parses or cleans the data.
"""

import uuid
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Query,
    Request,
    UploadFile,
    status,
)

from app.api.v1.schemas.dataset import DatasetResponse
from app.core.roles import Role
from app.dependencies.auth import RequireRoles, get_current_user
from app.dependencies.services import get_ingestion_service
from app.ingestion.cleaner import process_dataset
from app.models.user import User
from app.services.exceptions import AuthorizationError, ValidationError
from app.services.ingestion import IngestionService
from app.utils.response import api_response

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Upload Dataset",
    description=(
        "Stream a raw dataset file into storage, register it, and trigger the "
        "cleaning worker. Returns the created dataset_id and its status. "
        "Requires Admin or Dean."
    ),
)
async def upload_dataset(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Raw dataset file (csv, xlsx, xls, json)."),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: IngestionService = Depends(get_ingestion_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Enforce tenant isolation (Admins may target another tenant).
    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    if not file.filename:
        raise ValidationError(
            "No file was provided in the upload.",
            error_code="file_required",
        )

    result = await service.ingest_file(
        tenant_id=target_tenant_id,
        filename=file.filename,
        source=file,
    )
    dataset = result.data

    # Clean the file into student_metrics after the response is sent.
    background_tasks.add_task(
        process_dataset, dataset.dataset_id, target_tenant_id, dataset.storage_uri
    )

    data = DatasetResponse.model_validate(dataset).model_dump(mode="json")
    return api_response(
        success=True,
        message=result.message or "Dataset uploaded successfully.",
        data=data,
        request_id=req_id,
    )

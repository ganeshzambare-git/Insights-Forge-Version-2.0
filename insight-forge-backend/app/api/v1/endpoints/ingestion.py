"""
Insight Forge V2 — Ingestion Router.

Receives a raw tabular upload (CSV/JSON), stores it as a per-tenant dataset with
its rows, and returns the new dataset identifier plus a data-quality score.
"""

from typing import Any
import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_dataset_service
from app.models.user import User
from app.services.dataset import DatasetService
from app.services.exceptions import AuthorizationError, ValidationError
from app.api.v1.schemas.dataset import IngestionResponse
from app.utils.response import api_response

router = APIRouter(
    prefix="/ingestion",
    tags=["ingestion"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Ingest Dataset",
    description="Upload a CSV or JSON file; its rows are parsed and stored per tenant.",
)
async def ingest_dataset(
    request: Request,
    file: UploadFile = File(..., description="The CSV or JSON dataset file to store."),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin override only)."
    ),
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Enforce tenant isolation.
    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    filename = file.filename or "upload.csv"
    if not filename.lower().endswith((".csv", ".json")):
        raise ValidationError(
            "Only .csv and .json uploads are supported.",
            error_code="unsupported_format",
        )

    content = await file.read()
    result = await service.ingest(
        tenant_id=target_tenant_id, filename=filename, content=content
    )
    outcome = result.data
    dataset = outcome.dataset

    data = IngestionResponse(
        dataset_id=dataset.dataset_id,
        dataset_name=dataset.dataset_name,
        row_count=dataset.row_count or 0,
        column_count=len(outcome.columns),
        columns=outcome.columns,
        processing_status=dataset.processing_status,
        health_score=dataset.health_score,
    ).model_dump()

    return api_response(
        success=True,
        message=result.message or "Dataset ingested successfully.",
        data=data,
        request_id=req_id,
    )

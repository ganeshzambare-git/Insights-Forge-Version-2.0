"""
Insight Forge V2 — Data Cleaning Controller.

Exposes REST endpoint for executing dataset quality profiling and certification.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, UploadFile, File, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_cleaning_service
from app.models.user import User
from app.services.cleaning import CleaningService
from app.utils.response import api_response
from app.services.exceptions import AuthorizationError

router = APIRouter(prefix="/cleaning", tags=["cleaning"])


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Run Dataset Quality Analysis & Cleaning Recommendations",
    description="Upload a CSV or XLSX dataset to inspect quality issues, calculate scores, and generate audit recommendations.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def analyze_dataset(
    request: Request,
    file: UploadFile = File(..., description="The dataset CSV or XLSX file to clean."),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin override only)."
    ),
    current_user: User = Depends(get_current_user),
    service: CleaningService = Depends(get_cleaning_service),
) -> dict[str, Any]:
    """FastAPI endpoint running the data quality cleaning pipeline."""
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

    # Read uploaded file contents
    content = await file.read()

    # Trigger cleaning pipeline
    summary, log_entries = await service.run_cleaning_pipeline(
        tenant_id=target_tenant_id,
        file_content=content,
        filename=file.filename,
    )

    return api_response(
        success=True,
        message="Dataset quality analysis completed successfully.",
        data={
            "summary": summary.model_dump(),
            "cleaning_log": [log.model_dump() for log in log_entries],
        },
        request_id=req_id,
    )

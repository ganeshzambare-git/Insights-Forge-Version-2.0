"""
Insight Forge V2 — AI Pipeline Controller.

Exposes REST endpoint for triggering the multi-agent orchestrated workflow.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, UploadFile, File, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_ai_service
from app.models.user import User
from app.services.ai_service import AIService
from app.utils.response import api_response
from app.services.exceptions import AuthorizationError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Run AI Multi-Agent Analysis Pipeline",
    description="Upload a dataset file (CSV/JSON) and trigger the sequential Data Engineer, Analyst, Business Analyst, and Executive Report Generator pipeline.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def analyze_dataset(
    request: Request,
    file: UploadFile = File(..., description="The dataset CSV or JSON file to analyze."),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin override only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
) -> dict[str, Any]:
    """FastAPI endpoint running the multi-agent AI pipeline."""
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

    # Trigger orchestrator execution
    result = await service.run_ai_analysis(
        tenant_id=target_tenant_id,
        file_content=content,
        filename=file.filename,
    )

    return api_response(
        success=result.success,
        message="AI Analysis completed successfully." if result.success else "AI Analysis pipeline execution halted on step failure.",
        data=result.model_dump(),
        request_id=req_id,
    )

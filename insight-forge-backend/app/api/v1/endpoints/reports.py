"""
Insight Forge V2 — Reports Router.

Runs the deterministic multi-agent analysis pipeline over a stored dataset and
returns the consolidated executive report. No external LLM or mock data is used.
"""

from typing import Any
import uuid

from fastapi import APIRouter, Depends, Request, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_dataset_service
from app.models.user import User
from app.services.dataset import DatasetService
from app.utils.response import api_response

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


@router.get(
    "/{dataset_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Generate Dataset Report",
    description="Run the multi-agent analysis pipeline over a stored dataset's rows.",
)
async def generate_report(
    request: Request,
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DatasetService = Depends(get_dataset_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    result = await service.build_report(current_user.tenant_id, dataset_id)

    return api_response(
        success=result.success,
        message=(
            "Report generated successfully."
            if result.success
            else "Report pipeline halted on step failure."
        ),
        data=result.model_dump(),
        request_id=req_id,
    )

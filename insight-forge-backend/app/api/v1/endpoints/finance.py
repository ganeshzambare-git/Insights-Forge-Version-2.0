"""
Insight Forge V2 — Finance & Resource Allocation Router.

Exposes tenant-scoped budget ledger and utilization summary backed by the real
``budget_allocations`` table.
"""

from typing import Any
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_finance_service
from app.models.user import User
from app.services.finance_service import FinanceService
from app.utils.response import api_response

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get(
    "/resource-allocation",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Resource Allocation Data",
    description="Retrieve tenant-scoped budget allocations and utilization summary.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_resource_allocation(
    request: Request,
    dimension: str | None = Query(default=None, description="Organizational dimension filter."),
    current_user: User = Depends(get_current_user),
    service: FinanceService = Depends(get_finance_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    data = await service.resource_allocation(
        tenant_id=current_user.tenant_id, dimension=dimension
    )

    return api_response(
        success=True,
        message="Resource allocation data retrieved successfully.",
        data=data,
        request_id=req_id,
    )

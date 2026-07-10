"""
Insight Forge V2 — Finance & Resource Allocation Router.

Exposes tenant-scoped budget ledger and infrastructure utilization endpoints.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.models.user import User
from app.utils.response import api_response

router = APIRouter(prefix="/finance", tags=["finance"])


# ============================================================
# TASK 27 – Infrastructure Allocation & Financial Dashboard
# ============================================================

@router.get(
    "/resource-allocation",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Resource Allocation Data",
    description="Retrieve tenant-scoped budget allocations and infrastructure utilization summary.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_resource_allocation(
    request: Request,
    dimension: str | None = Query(default=None, description="Organizational dimension filter."),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    mock_budget_ledger = [
        {
            "allocation_id": str(uuid.uuid4()),
            "category": "Infrastructure",
            "description": "Cloud compute cluster reservation",
            "allocated_budget": 120000.00,
            "current_balance": 84300.00,
            "utilization_pct": 29.75,
            "fiscal_year": "FY-2026",
            "dimension": "Technology",
        },
        {
            "allocation_id": str(uuid.uuid4()),
            "category": "Faculty Resources",
            "description": "Academic staff compensation fund",
            "allocated_budget": 540000.00,
            "current_balance": 412000.00,
            "utilization_pct": 23.70,
            "fiscal_year": "FY-2026",
            "dimension": "Academic",
        },
        {
            "allocation_id": str(uuid.uuid4()),
            "category": "Student Services",
            "description": "Counselling, tutoring and welfare programs",
            "allocated_budget": 95000.00,
            "current_balance": 61250.00,
            "utilization_pct": 35.52,
            "fiscal_year": "FY-2026",
            "dimension": "Student Affairs",
        },
        {
            "allocation_id": str(uuid.uuid4()),
            "category": "Research & Development",
            "description": "Applied AI and data science research grants",
            "allocated_budget": 210000.00,
            "current_balance": 178500.00,
            "utilization_pct": 15.00,
            "fiscal_year": "FY-2026",
            "dimension": "Research",
        },
    ]

    if dimension:
        mock_budget_ledger = [b for b in mock_budget_ledger if b["dimension"] == dimension]

    total_allocated = sum(b["allocated_budget"] for b in mock_budget_ledger)
    total_balance = sum(b["current_balance"] for b in mock_budget_ledger)
    total_spent = total_allocated - total_balance
    overall_utilization = round((total_spent / total_allocated) * 100, 2) if total_allocated else 0.0

    utilization_cards = [
        {
            "label": "Total Allocated",
            "value": f"${total_allocated:,.2f}",
            "icon": "📊",
            "color": "#38bdf8",
        },
        {
            "label": "Current Balance",
            "value": f"${total_balance:,.2f}",
            "icon": "💰",
            "color": "#34d399",
        },
        {
            "label": "Total Spent",
            "value": f"${total_spent:,.2f}",
            "icon": "📉",
            "color": "#f59e0b",
        },
        {
            "label": "Overall Utilization",
            "value": f"{overall_utilization}%",
            "icon": "⚡",
            "color": "#a78bfa",
        },
    ]

    return api_response(
        success=True,
        message="Resource allocation data retrieved successfully.",
        data={
            "budget_ledger": mock_budget_ledger,
            "utilization_cards": utilization_cards,
            "financial_summary": {
                "total_allocated": total_allocated,
                "total_balance": total_balance,
                "total_spent": total_spent,
                "overall_utilization_pct": overall_utilization,
                "fiscal_year": "FY-2026",
                "tenant_id": str(current_user.tenant_id),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "filters_applied": {"dimension": dimension},
        },
        request_id=req_id,
    )

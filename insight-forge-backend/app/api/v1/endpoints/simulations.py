from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.models.user import User
from app.utils.response import api_response

router = APIRouter(
    prefix="/simulations",
    tags=["simulations"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)

class SimulationRequest(BaseModel):
    credit_ratio: float = Field(..., ge=0.0, le=1.0, description="Credit ratios explore parameters.")
    target_cohorts: int = Field(..., ge=1, le=100, description="Target student cohorts explorer sizes.")
    class_capacity: int = Field(..., ge=1, le=500, description="Class cap allocations limits.")

@router.post(
    "/project-curves",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Project Planning Curves",
    description="Asynchronously calculate predicted graduation curves based on sliders parameters.",
)
async def project_curves(
    request: Request,
    payload: SimulationRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Perform server-side math calculations for predictive trends
    c_ratio = payload.credit_ratio
    t_cohorts = payload.target_cohorts
    c_capacity = payload.class_capacity

    # Mock algorithm returning gpa, risk indices, and resource predictions
    projected_success_rate = round((c_ratio * 40) + (c_capacity / 10) + (100 - t_cohorts), 1)
    projected_success_rate = max(10.0, min(projected_success_rate, 99.9))

    estimated_gpa = round(2.0 + (c_ratio * 1.5) - (t_cohorts / 100) + (c_capacity / 500), 2)
    estimated_gpa = max(1.0, min(estimated_gpa, 4.0))

    trend_points = []
    base_val = estimated_gpa
    for step in range(5):
        trend_points.append({
            "step": f"T+{step * 3}m",
            "gpa": round(base_val - (step * 0.05) + (c_ratio * step * 0.08), 2)
        })

    data = {
        "success_rate": projected_success_rate,
        "average_gpa": estimated_gpa,
        "trend": trend_points,
        "input_parameters": {
            "credit_ratio": c_ratio,
            "target_cohorts": t_cohorts,
            "class_capacity": c_capacity
        },
        "computed_at": datetime.now(timezone.utc).isoformat()
    }

    return api_response(
        success=True,
        message="Simulation projections calculated successfully.",
        data=data,
        request_id=req_id,
    )

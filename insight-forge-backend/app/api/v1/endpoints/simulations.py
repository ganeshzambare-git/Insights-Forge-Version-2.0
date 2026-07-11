"""
Insight Forge V2 — Planning Simulation Router.

Projects planning curves from the tenant's *real* academic baseline (current
average GPA / attendance from student_metrics) adjusted by the what-if sliders.
"""

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_student_metric_service
from app.models.user import User
from app.services.student_metric import StudentMetricService
from app.utils.response import api_response

router = APIRouter(
    prefix="/simulations",
    tags=["simulations"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)


class SimulationRequest(BaseModel):
    credit_ratio: float = Field(..., ge=0.0, le=1.0, description="Credit ratio parameter.")
    target_cohorts: int = Field(..., ge=1, le=100, description="Target cohort count.")
    class_capacity: int = Field(..., ge=1, le=500, description="Class capacity limit.")


@router.post(
    "/project-curves",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Project Planning Curves",
    description="Project graduation/GPA curves from the tenant's real baseline and slider inputs.",
)
async def project_curves(
    request: Request,
    payload: SimulationRequest,
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    baseline = await service.tenant_baseline(current_user.tenant_id)
    base_gpa = baseline["avg_gpa"] or 2.5
    base_attendance = baseline["avg_attendance"] or 80.0

    c_ratio = payload.credit_ratio
    t_cohorts = payload.target_cohorts
    c_capacity = payload.class_capacity

    # Deterministic projection: start from the real baseline, then apply the
    # sliders as bounded adjustments.
    capacity_factor = min(c_capacity, 200) / 200.0  # smaller classes help
    load_penalty = min(t_cohorts, 50) / 200.0  # more cohorts spread resources thin

    estimated_gpa = base_gpa + (c_ratio * 0.6) + (capacity_factor * 0.4) - load_penalty
    estimated_gpa = round(max(1.0, min(estimated_gpa, 4.0)), 2)

    projected_success_rate = round(
        min(99.9, max(10.0, (base_attendance * 0.6) + (estimated_gpa / 4.0 * 40)
                      + (capacity_factor * 10) - (load_penalty * 10))),
        1,
    )

    trend = []
    for step in range(5):
        val = estimated_gpa + (c_ratio * step * 0.05) - (load_penalty * step * 0.04)
        trend.append({"step": f"T+{step * 3}m", "gpa": round(max(1.0, min(val, 4.0)), 2)})

    data = {
        "success_rate": projected_success_rate,
        "average_gpa": estimated_gpa,
        "trend": trend,
        "baseline": baseline,
        "input_parameters": {
            "credit_ratio": c_ratio,
            "target_cohorts": t_cohorts,
            "class_capacity": c_capacity,
        },
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    return api_response(
        success=True,
        message="Simulation projections calculated successfully.",
        data=data,
        request_id=req_id,
    )

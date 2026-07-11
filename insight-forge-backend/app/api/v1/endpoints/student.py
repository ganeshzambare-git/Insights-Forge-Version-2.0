from typing import Any
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_student_metric_service
from app.models.user import User
from app.services.student_metric import StudentMetricService
from app.utils.response import api_response

router = APIRouter(
    prefix="/student",
    tags=["student"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY, Role.STUDENT))],
)


@router.get(
    "/progress-summary",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Student Progress Summary",
    description="Retrieve the authenticated student's real progress summary from their metrics.",
)
async def get_progress_summary(
    request: Request,
    term: str = Query(default="Fall 2026", description="Scope target term academic logs."),
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # "EmptyTerm" preserves the frontend's empty-ledger placeholder test.
    scoped_term = None if term in ("EmptyTerm", "", "All") else term

    data = await service.student_progress(
        tenant_id=current_user.tenant_id,
        student_id=current_user.user_id,
        term=scoped_term,
    )

    message = (
        "Student progress summary ledger is empty."
        if data.get("ledger_empty")
        else "Student progress summary retrieved successfully."
    )
    return api_response(success=True, message=message, data=data, request_id=req_id)


@router.get(
    "/normalized-grades",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Student Normalized Grades Distribution",
    description="Retrieve the authenticated student's GPA trend against their cohort average.",
)
async def get_normalized_grades(
    request: Request,
    term: str = Query(default="Fall 2026", description="Scope target term performance charts."),
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    history = await service.student_gpa_history(
        tenant_id=current_user.tenant_id,
        student_id=current_user.user_id,
    )
    data = {"term": term, **history}

    return api_response(
        success=True,
        message="Student normalized grade distributions retrieved successfully.",
        data=data,
        request_id=req_id,
    )

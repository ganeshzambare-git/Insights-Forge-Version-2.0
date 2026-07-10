from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.models.user import User
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
    description="Retrieve personal progress summary and modules logs for the authenticated student user.",
)
async def get_progress_summary(
    request: Request,
    term: str = Query(default="Fall 2026", description="Scope target term academic logs."),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # If mock empty term selected, return empty records to test Task 19 placeholder
    if term == "EmptyTerm":
        return api_response(
            success=True,
            message="Student progress summary ledger is empty.",
            data={
                "gpa": 0.0,
                "attendance_rate": 0,
                "ledger_empty": True,
                "records": [],
                "term": term
            },
            request_id=req_id,
        )

    # Standard Mock student progress payloads
    data = {
        "gpa": 3.65,
        "attendance_rate": 96,
        "ledger_empty": False,
        "term": term,
        "records": [
            {"subject": "Advanced Calculus", "grade": "A-", "score": 92},
            {"subject": "Software Engineering Principles", "grade": "A", "score": 95},
            {"subject": "Machine Learning Foundation", "grade": "B+", "score": 88},
            {"subject": "Academic Seminar", "grade": "Pass", "score": 100}
        ],
        "attendance_history": [
            {"date": "2026-10-01", "status": "Present"},
            {"date": "2026-10-02", "status": "Present"},
            {"date": "2026-10-03", "status": "Absent"},
            {"date": "2026-10-04", "status": "Present"},
            {"date": "2026-10-05", "status": "Present"}
        ],
        "study_modules": [
            {"name": "Neural Networks Backpropagation", "status": "Recommended", "duration": "4h"},
            {"name": "React Custom Virtualization hooks", "status": "Completed", "duration": "2h"}
        ]
    }

    return api_response(
        success=True,
        message="Student progress summary retrieved successfully.",
        data=data,
        request_id=req_id,
    )

@router.get(
    "/normalized-grades",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Student Normalized Grades Distribution",
    description="Retrieve normalized performance comparisons against student cohorts. Scoped to authenticated user.",
)
async def get_normalized_grades(
    request: Request,
    term: str = Query(default="Fall 2026", description="Scope target term performance charts."),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Shift mocks slightly based on term filter to verify chart redraws
    val_offset = 0.2 if term == "Spring 2026" else 0.0

    data = {
        "term": term,
        "student_gpa_history": [
            {"label": "T1 (W1)", "val": round(3.2 + val_offset, 2)},
            {"label": "T2 (W4)", "val": round(3.4 + val_offset, 2)},
            {"label": "T3 (W8)", "val": round(3.6 + val_offset, 2)},
            {"label": "T4 (W12)", "val": round(3.8 + val_offset, 2)}
        ],
        "cohort_gpa_history": [
            {"label": "T1 (W1)", "val": 3.0},
            {"label": "T2 (W4)", "val": 3.1},
            {"label": "T3 (W8)", "val": 3.2},
            {"label": "T4 (W12)", "val": 3.3}
        ]
    }

    return api_response(
        success=True,
        message="Student normalized grade distributions retrieved successfully.",
        data=data,
        request_id=req_id,
    )

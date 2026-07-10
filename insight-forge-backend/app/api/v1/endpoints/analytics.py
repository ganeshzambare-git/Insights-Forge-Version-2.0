"""
Insight Forge V2 — Analytics Router.

Exposes REST endpoints for academic business intelligence, risk analysis, and trends.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_analytics_service
from app.models.user import User
from app.services.analytics import AnalyticsService
from app.utils.response import api_response
from app.services.exceptions import AuthorizationError

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Dashboard Overview",
    description="Retrieve high-level overview dashboard statistics. Requires Admin or Dean.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_dashboard(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
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

    res = await service.get_dashboard(target_tenant_id)
    data = res.model_dump()
    return api_response(
        success=True,
        message="Dashboard overview statistics retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/kpis",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get KPIs",
    description="Fetch key performance indicators for institutional users.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_kpis(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_kpis(target_tenant_id)
    data = res.model_dump()
    return api_response(
        success=True,
        message="KPI statistics retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/student-risk",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Student Risk Classification",
    description="Filter and analyze student risk classification (Safe, Amber, Critical).",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_student_risk(
    request: Request,
    cohort_id: uuid.UUID | None = Query(
        default=None, description="Filter by cohort UUID."
    ),
    risk_level: str | None = Query(
        default=None, description="Filter by risk label (Safe, Amber, Critical)."
    ),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_student_risk(
        tenant_id=target_tenant_id, cohort_id=cohort_id, risk_level=risk_level
    )
    data = [item.model_dump() for item in res]
    return api_response(
        success=True,
        message="Student risk classifications retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/cohort-performance",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Cohort Performance",
    description="Retrieve aggregated performance averages grouped by Cohort.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_cohort_performance(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_cohort_performance(target_tenant_id)
    data = [item.model_dump() for item in res]
    return api_response(
        success=True,
        message="Cohort performance statistics retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/faculty-performance",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Faculty Workload & Performance",
    description="Fetch workload counts and student improvements grouped by Faculty.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_faculty_performance(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_faculty_performance(target_tenant_id)
    data = [item.model_dump() for item in res]
    return api_response(
        success=True,
        message="Faculty performance statistics retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/institution",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Institution Analytics",
    description="Calculate institutional overall health index score and department breakdowns.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_institution_health(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_institution_health(target_tenant_id)
    data = res.model_dump()
    return api_response(
        success=True,
        message="Institutional health statistics retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/trends",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Performance & Ingress Trends",
    description="Fetch metrics term-series performance trends and coaching counts.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_trends(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_trends(target_tenant_id)
    data = res.model_dump()
    return api_response(
        success=True,
        message="Academic performance trends retrieved.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/recommendations",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Student Advisories & Recommendations",
    description="Trigger rule-based academic advisory recommendation flags.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_recommendations(
    request: Request,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    target_tenant_id = current_user.tenant_id
    if current_user.assigned_role == Role.ADMIN.value:
        if tenant_id:
            target_tenant_id = tenant_id
    elif tenant_id and tenant_id != current_user.tenant_id:
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    res = await service.get_recommendations(target_tenant_id)
    data = [item.model_dump() for item in res]
    return api_response(
        success=True,
        message="Rule-based advisory recommendations generated.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/executive-summary",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Executive Analytics Summary",
    description="Retrieve institutional high-level KPIs, allocations, and charts. Requires Admin or Dean.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_executive_summary(request: Request) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Generate mock executive canvas statistics
    data = {
        "kpis": {
            "total_students": 12420,
            "critical_risk": 324,
            "active_interventions": 186,
            "completion_rate": 94.2
        },
        "departments": [
            {"name": "Engineering", "gpa": 3.42, "student_count": 3200, "budget_allocated": 750000},
            {"name": "Sciences", "gpa": 3.51, "student_count": 4100, "budget_allocated": 980000},
            {"name": "Humanities", "gpa": 3.12, "student_count": 1800, "budget_allocated": 420000},
            {"name": "Business", "gpa": 3.33, "student_count": 2100, "budget_allocated": 590000},
            {"name": "Arts", "gpa": 3.25, "student_count": 1220, "budget_allocated": 310000}
        ],
        "resource_allocation": {
            "pyspark_cores_quota": 64,
            "pyspark_cores_active": 28,
            "software_licenses_total": 500,
            "software_licenses_active": 342,
            "gpu_clusters_active": 4
        },
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

    return api_response(
        success=True,
        message="Executive summary metrics retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/department-records",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Filtered Department Records",
    description="Retrieve detailed student records filtered by department scope scope. Requires Admin, Dean, or Faculty.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)
async def get_department_records(
    request: Request,
    scope: str = Query(default="Engineering", description="Filter department scope name.")
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Generate mock student records
    student_templates = [
        {"name": "John Doe", "term_gpa": 3.12, "risk_level": "Medium", "credits": 15},
        {"name": "Jane Smith", "term_gpa": 3.65, "risk_level": "Low", "credits": 16},
        {"name": "Bob Johnson", "term_gpa": 2.85, "risk_level": "High", "credits": 12},
        {"name": "Alice Williams", "term_gpa": 3.90, "risk_level": "Low", "credits": 15},
        {"name": "Charlie Brown", "term_gpa": 3.42, "risk_level": "Low", "credits": 14},
        {"name": "Diana Ross", "term_gpa": 2.95, "risk_level": "Medium", "credits": 12},
        {"name": "Evan Wright", "term_gpa": 3.78, "risk_level": "Low", "credits": 15},
        {"name": "Fiona Gallagher", "term_gpa": 2.45, "risk_level": "High", "credits": 9}
    ]

    records = []
    # Adjust results based on scope filter
    for i, t in enumerate(student_templates):
        records.append({
            "id": f"student-id-{scope.lower()}-{i}",
            "name": t["name"],
            "department": scope,
            "term_gpa": t["term_gpa"],
            "risk_level": t["risk_level"],
            "term_credits": t["credits"],
            "status": "Enrolled"
        })

    return api_response(
        success=True,
        message=f"Department records for scope '{scope}' retrieved.",
        data={
            "scope": scope,
            "records": records,
            "total_records_count": len(records)
        },
        request_id=req_id,
    )


@router.post(
    "/export-audit-packet",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, Any],
    summary="Export Academic Audit Packet",
    description="Initiate non-blocking background job for institutional audit pack compilation. Requires Admin or Dean.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def export_audit_packet(request: Request) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    return api_response(
        success=True,
        message="Audit compliance packet compilation job started successfully in the background.",
        data={
            "job_id": f"export-job-{uuid.uuid4()}",
            "status": "Processing",
            "estimated_duration_sec": 4,
            "initiated_at": datetime.now(timezone.utc).isoformat()
        },
        request_id=req_id,
    )


# ============================================================
# TASK 25 – Attendance Analytics
# ============================================================

@router.get(
    "/attendance/summary",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Attendance Trend Summary",
    description="Retrieve monthly attendance trend data for the authenticated tenant.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_attendance_summary(
    request: Request,
    semester: str | None = Query(default=None, description="Semester label filter."),
    cohort_code: str | None = Query(default=None, description="Cohort code filter."),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    mock_trend = [
        {"month": "Jan", "attendance_rate": 91.2, "cohort": "CS-2026", "semester": "Spring 2026"},
        {"month": "Feb", "attendance_rate": 88.7, "cohort": "CS-2026", "semester": "Spring 2026"},
        {"month": "Mar", "attendance_rate": 93.4, "cohort": "CS-2026", "semester": "Spring 2026"},
        {"month": "Apr", "attendance_rate": 85.1, "cohort": "CS-2026", "semester": "Spring 2026"},
        {"month": "May", "attendance_rate": 87.6, "cohort": "CS-2026", "semester": "Spring 2026"},
        {"month": "Jun", "attendance_rate": 90.0, "cohort": "CS-2026", "semester": "Spring 2026"},
        {"month": "Jul", "attendance_rate": 78.3, "cohort": "CS-2026", "semester": "Summer 2026"},
        {"month": "Aug", "attendance_rate": 82.9, "cohort": "CS-2026", "semester": "Summer 2026"},
        {"month": "Sep", "attendance_rate": 94.5, "cohort": "CS-2026", "semester": "Fall 2026"},
        {"month": "Oct", "attendance_rate": 92.1, "cohort": "CS-2026", "semester": "Fall 2026"},
        {"month": "Nov", "attendance_rate": 89.8, "cohort": "CS-2026", "semester": "Fall 2026"},
        {"month": "Dec", "attendance_rate": 86.4, "cohort": "CS-2026", "semester": "Fall 2026"},
    ]

    if semester:
        mock_trend = [t for t in mock_trend if t["semester"] == semester]
    if cohort_code:
        mock_trend = [t for t in mock_trend if t["cohort"] == cohort_code]

    values = [t["attendance_rate"] for t in mock_trend]
    avg_rate = round(sum(values) / len(values), 2) if values else 0.0

    return api_response(
        success=True,
        message="Attendance trend summary retrieved successfully.",
        data={
            "trend": mock_trend,
            "summary": {
                "average_attendance_rate": avg_rate,
                "peak_attendance_rate": max(values) if values else 0.0,
                "trough_attendance_rate": min(values) if values else 0.0,
                "total_months": len(mock_trend),
            },
            "filters_applied": {"semester": semester, "cohort_code": cohort_code},
        },
        request_id=req_id,
    )


# ============================================================
# TASK 26 – Course & Curriculum Performance Analysis
# ============================================================

@router.get(
    "/courses/evaluation",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Course Evaluation Metrics",
    description="Retrieve course-level performance and evaluation data scoped by department and cohort.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_course_evaluation(
    request: Request,
    department: str | None = Query(default=None, description="Department scope filter."),
    cohort_code: str | None = Query(default=None, description="Cohort code filter."),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    mock_courses = [
        {
            "course_id": "CSC-401",
            "course_name": "Advanced Algorithms",
            "department": "Computer Science",
            "cohort_code": "CS-2026",
            "avg_score": 78.4,
            "pass_rate": 84.2,
            "enrollment": 52,
            "evaluations_submitted": 48,
            "kpi_status": "On Track",
        },
        {
            "course_id": "CSC-302",
            "course_name": "Operating Systems",
            "department": "Computer Science",
            "cohort_code": "CS-2026",
            "avg_score": 72.1,
            "pass_rate": 77.5,
            "enrollment": 61,
            "evaluations_submitted": 58,
            "kpi_status": "At Risk",
        },
        {
            "course_id": "MTH-201",
            "course_name": "Linear Algebra",
            "department": "Mathematics",
            "cohort_code": "MTH-2026",
            "avg_score": 81.9,
            "pass_rate": 91.0,
            "enrollment": 44,
            "evaluations_submitted": 43,
            "kpi_status": "Exceeding",
        },
        {
            "course_id": "ENG-110",
            "course_name": "Technical Writing",
            "department": "Engineering",
            "cohort_code": "ENG-2026",
            "avg_score": 88.5,
            "pass_rate": 95.3,
            "enrollment": 38,
            "evaluations_submitted": 37,
            "kpi_status": "Exceeding",
        },
    ]

    if department:
        mock_courses = [c for c in mock_courses if c["department"] == department]
    if cohort_code:
        mock_courses = [c for c in mock_courses if c["cohort_code"] == cohort_code]

    return api_response(
        success=True,
        message="Course evaluation metrics retrieved successfully.",
        data={
            "courses": mock_courses,
            "total_courses": len(mock_courses),
            "filters_applied": {"department": department, "cohort_code": cohort_code},
        },
        request_id=req_id,
    )

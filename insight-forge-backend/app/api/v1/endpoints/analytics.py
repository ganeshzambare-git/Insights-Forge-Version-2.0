"""
Insight Forge V2 — Analytics Router.

Exposes REST endpoints for academic business intelligence, risk analysis, and trends.
"""

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

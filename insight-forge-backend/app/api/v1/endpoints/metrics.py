"""
Insight Forge V2 — Metrics Router.

Exposes REST CRUD endpoints governing Student Metrics, scoped by active tenant partition.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_student_metric_service
from app.models.user import User
from app.services.student_metric import StudentMetricService
from app.api.v1.schemas.metric import (
    StudentMetricCreate,
    StudentMetricUpdate,
    StudentMetricResponse,
)
from app.utils.response import api_response
from app.services.exceptions import NotFoundError, AuthorizationError

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Create Student Metric",
    description="Log a new academic performance and attendance record for a student.",
)
async def create_metric(
    request: Request,
    payload: StudentMetricCreate,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
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

    result = await service.add_metric(
        tenant_id=target_tenant_id,
        student_user_id=payload.student_id,
        cohort_id=payload.cohort_id,
        raw_average_grade=payload.gpa,
        normalized_grade_score=None,
        attendance_percentage=payload.attendance_rate,
        success_indicator_status=payload.status_indicator,
        reporting_period=payload.academic_year,
    )

    db_obj = result.data
    data = StudentMetricResponse(
        metric_id=db_obj.metric_id,
        tenant_id=db_obj.tenant_id,
        student_id=db_obj.student_user_id,
        cohort_id=db_obj.cohort_id,
        academic_year=db_obj.reporting_period,
        gpa=db_obj.raw_average_grade,
        attendance_rate=db_obj.attendance_percentage,
        status_indicator=db_obj.success_indicator_status,
    ).model_dump()

    return api_response(
        success=True,
        message=result.message or "Student performance metric logged.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/{metric_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Student Metric",
    description="Retrieve specific performance metric details by integer ID.",
)
async def get_metric(
    request: Request,
    metric_id: int,
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    metric = await service.get_metric(metric_id)
    if not metric:
        raise NotFoundError(
            f"Student metric with ID '{metric_id}' not found.",
            error_code="metric_not_found",
        )

    # Tenant isolation check
    if (
        current_user.assigned_role != Role.ADMIN.value
        and metric.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    data = StudentMetricResponse(
        metric_id=metric.metric_id,
        tenant_id=metric.tenant_id,
        student_id=metric.student_user_id,
        cohort_id=metric.cohort_id,
        academic_year=metric.reporting_period,
        gpa=metric.raw_average_grade,
        attendance_rate=metric.attendance_percentage,
        status_indicator=metric.success_indicator_status,
    ).model_dump()

    return api_response(
        success=True,
        message="Student metric retrieved.",
        data=data,
        request_id=req_id,
    )


@router.patch(
    "/{metric_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Update Student Metric",
    description="Partially update a metric log. Enforces tenant boundaries.",
)
async def update_metric(
    request: Request,
    metric_id: int,
    payload: StudentMetricUpdate,
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Fetch metric to verify isolation
    metric = await service.get_metric(metric_id)
    if not metric:
        raise NotFoundError(
            f"Student metric with ID '{metric_id}' not found.",
            error_code="metric_not_found",
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and metric.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    result = await service.update_metric(
        metric_id=metric_id,
        raw_average_grade=payload.gpa,
        normalized_grade_score=None,
        attendance_percentage=payload.attendance_rate,
        success_indicator_status=payload.status_indicator,
        reporting_period=payload.academic_year,
    )

    db_obj = result.data
    data = StudentMetricResponse(
        metric_id=db_obj.metric_id,
        tenant_id=db_obj.tenant_id,
        student_id=db_obj.student_user_id,
        cohort_id=db_obj.cohort_id,
        academic_year=db_obj.reporting_period,
        gpa=db_obj.raw_average_grade,
        attendance_rate=db_obj.attendance_percentage,
        status_indicator=db_obj.success_indicator_status,
    ).model_dump()

    return api_response(
        success=True,
        message=result.message or "Student performance metric updated.",
        data=data,
        request_id=req_id,
    )


@router.delete(
    "/{metric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Student Metric",
    description="Remove performance metric record.",
)
async def delete_metric(
    metric_id: int,
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
) -> None:
    # Fetch metric to verify isolation
    metric = await service.get_metric(metric_id)
    if not metric:
        raise NotFoundError(
            f"Student metric with ID '{metric_id}' not found.",
            error_code="metric_not_found",
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and metric.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    await service.delete_metric(metric_id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Student Metrics",
    description="List student performance metrics. Filter by status, student, or cohort.",
)
async def list_metrics(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    student_id: uuid.UUID | None = Query(
        default=None, description="Filter by Student user UUID."
    ),
    cohort_id: uuid.UUID | None = Query(
        default=None, description="Filter by Cohort UUID."
    ),
    status_indicator: str | None = Query(
        default=None, description="Filter status (Safe, Amber, Critical)."
    ),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: StudentMetricService = Depends(get_student_metric_service),
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

    # Resolve metric lists based on query context
    if student_id:
        metrics = await service.get_metrics(
            tenant_id=target_tenant_id, student_id=student_id
        )
    else:
        metrics = await service.latest_metrics(tenant_id=target_tenant_id, limit=limit)

    # Perform filter matching in memory
    filtered = []
    for m in metrics:
        if cohort_id and m.cohort_id != cohort_id:
            continue
        if status_indicator and m.success_indicator_status != status_indicator:
            continue
        filtered.append(m)

    # Apply manual pagination offset and limit to the matching list
    paged = filtered[offset : offset + limit]

    data = []
    for db_obj in paged:
        data.append(
            StudentMetricResponse(
                metric_id=db_obj.metric_id,
                tenant_id=db_obj.tenant_id,
                student_id=db_obj.student_user_id,
                cohort_id=db_obj.cohort_id,
                academic_year=db_obj.reporting_period,
                gpa=db_obj.raw_average_grade,
                attendance_rate=db_obj.attendance_percentage,
                status_indicator=db_obj.success_indicator_status,
            ).model_dump()
        )

    meta = {
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(filtered),
        }
    }
    return api_response(
        success=True,
        message="Metrics listed successfully.",
        data=data,
        meta=meta,
        request_id=req_id,
    )

"""
Insight Forge V2 — Coaching Interventions Router.

Exposes REST CRUD endpoints governing Coaching Interventions, tenant-isolated.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, Query, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.dependencies.services import get_coaching_intervention_service
from app.models.user import User
from app.services.coaching_intervention import CoachingInterventionService
from app.api.v1.schemas.intervention import (
    CoachingInterventionCreate,
    CoachingInterventionUpdate,
    CoachingInterventionResponse,
)
from app.utils.response import api_response
from app.services.exceptions import NotFoundError, AuthorizationError

router = APIRouter(
    prefix="/interventions",
    tags=["interventions"],
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN, Role.FACULTY))],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Create Intervention",
    description="Record a new student coaching intervention.",
)
async def create_intervention(
    request: Request,
    payload: CoachingInterventionCreate,
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: CoachingInterventionService = Depends(get_coaching_intervention_service),
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

    result = await service.create_intervention(
        tenant_id=target_tenant_id,
        student_user_id=payload.student_id,
        faculty_user_id=payload.advisor_id,
        intervention_notes=payload.intervention_notes,
    )

    db_obj = result.data
    data = CoachingInterventionResponse(
        intervention_id=db_obj.intervention_id,
        tenant_id=db_obj.tenant_id,
        student_id=db_obj.student_user_id,
        advisor_id=db_obj.faculty_user_id,
        intervention_notes=db_obj.intervention_notes,
        logged_at=db_obj.recorded_timestamp,
    ).model_dump()

    return api_response(
        success=True,
        message=result.message or "Coaching intervention logged successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/{intervention_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Intervention",
    description="Retrieve specific coaching intervention details by UUID.",
)
async def get_intervention(
    request: Request,
    intervention_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CoachingInterventionService = Depends(get_coaching_intervention_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    intervention = await service.get_intervention(intervention_id)
    if not intervention:
        raise NotFoundError(
            f"Coaching intervention with ID '{intervention_id}' not found.",
            error_code="intervention_not_found",
        )

    # Tenant isolation check
    if (
        current_user.assigned_role != Role.ADMIN.value
        and intervention.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    data = CoachingInterventionResponse(
        intervention_id=intervention.intervention_id,
        tenant_id=intervention.tenant_id,
        student_id=intervention.student_user_id,
        advisor_id=intervention.faculty_user_id,
        intervention_notes=intervention.intervention_notes,
        logged_at=intervention.recorded_timestamp,
    ).model_dump()

    return api_response(
        success=True,
        message="Coaching intervention retrieved.",
        data=data,
        request_id=req_id,
    )


@router.patch(
    "/{intervention_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Update Intervention",
    description="Update notes of an existing intervention. Enforces tenant boundaries.",
)
async def update_intervention(
    request: Request,
    intervention_id: uuid.UUID,
    payload: CoachingInterventionUpdate,
    current_user: User = Depends(get_current_user),
    service: CoachingInterventionService = Depends(get_coaching_intervention_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Fetch to verify tenant isolation
    intervention = await service.get_intervention(intervention_id)
    if not intervention:
        raise NotFoundError(
            f"Coaching intervention with ID '{intervention_id}' not found.",
            error_code="intervention_not_found",
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and intervention.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    notes = payload.intervention_notes if payload.intervention_notes else ""
    result = await service.update_intervention(
        intervention_id=intervention_id, intervention_notes=notes
    )

    db_obj = result.data
    data = CoachingInterventionResponse(
        intervention_id=db_obj.intervention_id,
        tenant_id=db_obj.tenant_id,
        student_id=db_obj.student_user_id,
        advisor_id=db_obj.faculty_user_id,
        intervention_notes=db_obj.intervention_notes,
        logged_at=db_obj.recorded_timestamp,
    ).model_dump()

    return api_response(
        success=True,
        message=result.message or "Coaching intervention updated.",
        data=data,
        request_id=req_id,
    )


@router.delete(
    "/{intervention_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Intervention",
    description="Remove coaching intervention log.",
)
async def delete_intervention(
    intervention_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CoachingInterventionService = Depends(get_coaching_intervention_service),
) -> None:
    # Fetch to verify tenant isolation
    intervention = await service.get_intervention(intervention_id)
    if not intervention:
        raise NotFoundError(
            f"Coaching intervention with ID '{intervention_id}' not found.",
            error_code="intervention_not_found",
        )

    if (
        current_user.assigned_role != Role.ADMIN.value
        and intervention.tenant_id != current_user.tenant_id
    ):
        raise AuthorizationError(
            "Access denied to target tenant partition.",
            error_code="tenant_forbidden",
        )

    await service.delete_intervention(intervention_id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Interventions",
    description="List coaching interventions. Filter by student, limit, or offset.",
)
async def list_interventions(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    student_id: uuid.UUID | None = Query(
        default=None, description="Filter by Student user UUID."
    ),
    tenant_id: uuid.UUID | None = Query(
        default=None, description="Scope tenant UUID (Admin only)."
    ),
    current_user: User = Depends(get_current_user),
    service: CoachingInterventionService = Depends(get_coaching_intervention_service),
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

    if student_id:
        interventions = await service.get_interventions_by_student(
            tenant_id=target_tenant_id, student_id=student_id
        )
    else:
        interventions = await service.get_recent_interventions(
            tenant_id=target_tenant_id, limit=limit
        )

    # Perform filter mapping and paging in memory
    filtered = list(interventions)
    paged = filtered[offset : offset + limit]

    data = []
    for db_obj in paged:
        data.append(
            CoachingInterventionResponse(
                intervention_id=db_obj.intervention_id,
                tenant_id=db_obj.tenant_id,
                student_id=db_obj.student_user_id,
                advisor_id=db_obj.faculty_user_id,
                intervention_notes=db_obj.intervention_notes,
                logged_at=db_obj.recorded_timestamp,
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
        message="Interventions listed successfully.",
        data=data,
        meta=meta,
        request_id=req_id,
    )


# ============================================================
# FUTURE BULK INTERVENTIONS HOOKS (DOCUMENTATION & COMMENTS ONLY)
# ============================================================
# TODO: Future bulk import of coaching intervention logs:
# POST /interventions/bulk
#   - payload: InterventionsBulkImportRequest
#   - role: Faculty / Dean / Admin
#   - execution: FastAPI BackgroundTasks or asyncio batch processing

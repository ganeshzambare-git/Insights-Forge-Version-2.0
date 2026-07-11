"""
Insight Forge V2 — Background Task Status Router.

Reads real background job records from the ``background_tasks`` table. Jobs are
created and advanced by FastAPI BackgroundTasks (see app.workers.task_runner) —
no Celery/Redis.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Path, Request, status

from app.core.roles import Role
from app.dependencies.auth import RequireRoles, get_current_user
from app.dependencies.services import get_task_service
from app.models.background_task import BackgroundTask
from app.models.user import User
from app.services.task_service import TaskService
from app.utils.response import api_response

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _serialize(task: BackgroundTask) -> dict[str, Any]:
    return {
        "task_id": str(task.task_id),
        "task_type": task.task_type,
        "status": task.status,
        "progress_pct": task.progress_pct,
        "started_at": _iso(task.started_at),
        "completed_at": _iso(task.completed_at),
        "timeline": task.timeline,
        "result": task.result,
        "error": task.error,
    }


@router.get(
    "/status/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Background Task Status",
    description="Retrieve current execution status, progress, and result of a background task.",
    dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))],
)
async def get_task_status(
    request: Request,
    task_id: str = Path(..., description="Task identifier to retrieve status for."),
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    task = None
    try:
        task = await service.get_task(uuid.UUID(task_id))
    except ValueError:
        task = None

    if not task or task.tenant_id != current_user.tenant_id:
        # Unknown / cross-tenant id → report a neutral Pending placeholder.
        data = {
            "task_id": task_id,
            "task_type": "UNKNOWN",
            "status": "Pending",
            "progress_pct": 0,
            "started_at": None,
            "completed_at": None,
            "timeline": [],
            "result": None,
            "error": None,
        }
        return api_response(
            success=True,
            message=f"No active task found for task_id: {task_id}.",
            data=data,
            request_id=req_id,
        )

    return api_response(
        success=True,
        message=f"Task status retrieved for task_id: {task_id}.",
        data=_serialize(task),
        request_id=req_id,
    )


@router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List All Background Tasks",
    description="Retrieve a summary list of the tenant's background tasks.",
    dependencies=[Depends(RequireRoles(Role.ADMIN))],
)
async def list_tasks(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    tasks = await service.list_tasks(current_user.tenant_id)
    summaries = [
        {
            "task_id": str(t.task_id),
            "task_type": t.task_type,
            "status": t.status,
            "progress_pct": t.progress_pct,
            "started_at": _iso(t.started_at),
        }
        for t in tasks
    ]

    return api_response(
        success=True,
        message="Task list retrieved successfully.",
        data={"tasks": summaries, "total": len(summaries)},
        request_id=req_id,
    )

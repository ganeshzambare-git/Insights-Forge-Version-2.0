"""
Insight Forge V2 — Background Task Status Router.

Exposes the task lifecycle status endpoint for long-running backend jobs.
"""

from typing import Any
import uuid
import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request, Path, status

from app.core.roles import Role
from app.dependencies.auth import get_current_user, RequireRoles
from app.models.user import User
from app.utils.response import api_response

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Simulated in-process task store (stateless across requests — mock only).
_MOCK_TASK_STATES = {
    "task-running-001": {
        "task_id": "task-running-001",
        "task_type": "ML_RISK_PIPELINE",
        "status": "Running",
        "progress_pct": 62,
        "started_at": (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat(),
        "completed_at": None,
        "timeline": [
            {"event": "Queued",  "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=4)).isoformat()},
            {"event": "Started", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()},
            {"event": "Processing cohort partition CS-2026", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()},
        ],
        "result": None,
        "error": None,
    },
    "task-completed-002": {
        "task_id": "task-completed-002",
        "task_type": "AUDIT_EXPORT",
        "status": "Completed",
        "progress_pct": 100,
        "started_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(minutes=55)).isoformat(),
        "timeline": [
            {"event": "Queued",    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()},
            {"event": "Started",   "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=62)).isoformat()},
            {"event": "Completed", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=55)).isoformat()},
        ],
        "result": {
            "download_url": "/exports/audit-export-20260710.csv",
            "record_count": 1840,
            "file_size_kb": 214,
        },
        "error": None,
    },
    "task-failed-003": {
        "task_id": "task-failed-003",
        "task_type": "DATA_INGESTION",
        "status": "Failed",
        "progress_pct": 38,
        "started_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(minutes=115)).isoformat(),
        "timeline": [
            {"event": "Queued",  "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()},
            {"event": "Started", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=118)).isoformat()},
            {"event": "Failed",  "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=115)).isoformat()},
        ],
        "result": None,
        "error": {
            "code": "CSV_SCHEMA_MISMATCH",
            "message": "Uploaded file column headers do not match expected schema.",
            "recovery": "Re-upload the file using the validated CSV template from the ingestion documentation.",
        },
    },
}


# ============================================================
# TASK 28 – Background Task Status
# ============================================================

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
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    task = _MOCK_TASK_STATES.get(task_id)
    if not task:
        # Return a dynamic 'Pending' state for any unknown task_id
        task = {
            "task_id": task_id,
            "task_type": "UNKNOWN",
            "status": "Pending",
            "progress_pct": 0,
            "started_at": None,
            "completed_at": None,
            "timeline": [
                {"event": "Queued", "timestamp": datetime.now(timezone.utc).isoformat()}
            ],
            "result": None,
            "error": None,
        }

    return api_response(
        success=True,
        message=f"Task status retrieved for task_id: {task_id}.",
        data=task,
        request_id=req_id,
    )


@router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List All Background Tasks",
    description="Retrieve a summary list of all known background tasks.",
    dependencies=[Depends(RequireRoles(Role.ADMIN))],
)
async def list_tasks(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    task_summaries = [
        {
            "task_id": t["task_id"],
            "task_type": t["task_type"],
            "status": t["status"],
            "progress_pct": t["progress_pct"],
            "started_at": t["started_at"],
        }
        for t in _MOCK_TASK_STATES.values()
    ]

    return api_response(
        success=True,
        message="Task list retrieved successfully.",
        data={"tasks": task_summaries, "total": len(task_summaries)},
        request_id=req_id,
    )

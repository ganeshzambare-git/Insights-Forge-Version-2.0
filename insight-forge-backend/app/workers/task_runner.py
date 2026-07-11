"""
Insight Forge V2 — Background Task Runner Helpers.

Standalone async helpers that update a ``background_tasks`` row from a FastAPI
``BackgroundTasks`` callback. They open their own short-lived session (the
request session is closed by the time the callback runs) and are RLS-scoped to
the tenant. This is the Celery-free execution path for the platform.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.enums import TaskStatus
from app.db.session import async_session_maker
from app.models.background_task import BackgroundTask

logger = logging.getLogger("app.workers.task_runner")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _load(session, task_id: uuid.UUID) -> BackgroundTask | None:
    return await session.get(BackgroundTask, task_id)


async def _with_task(tenant_id: uuid.UUID, task_id: uuid.UUID, mutate) -> None:
    """Open a tenant-scoped session, apply ``mutate(task)``, and commit."""
    try:
        async with async_session_maker() as session:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :t, true)"),
                {"t": str(tenant_id)},
            )
            task = await _load(session, task_id)
            if task is None:
                logger.warning("Task %s not found for update", task_id)
                return
            mutate(task)
            await session.commit()
    except Exception:  # background updates must never crash the request lifecycle
        logger.exception("Failed to update task %s", task_id)


async def start_task(
    tenant_id: uuid.UUID, task_id: uuid.UUID, event: str = "Started"
) -> None:
    """Mark a task Running and stamp its start time."""

    def mutate(task: BackgroundTask) -> None:
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.now(timezone.utc)
        task.timeline = list(task.timeline) + [{"event": event, "timestamp": _now()}]

    await _with_task(tenant_id, task_id, mutate)


async def update_progress(
    tenant_id: uuid.UUID, task_id: uuid.UUID, progress_pct: int, event: str
) -> None:
    """Update a task's progress percentage and append a timeline entry."""

    def mutate(task: BackgroundTask) -> None:
        task.progress_pct = max(0, min(100, progress_pct))
        task.timeline = list(task.timeline) + [{"event": event, "timestamp": _now()}]

    await _with_task(tenant_id, task_id, mutate)


async def complete_task(
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
    result: dict | None = None,
    event: str = "Completed",
) -> None:
    """Mark a task Completed with an optional result payload."""

    def mutate(task: BackgroundTask) -> None:
        task.status = TaskStatus.COMPLETED.value
        task.progress_pct = 100
        task.result = result
        task.completed_at = datetime.now(timezone.utc)
        task.timeline = list(task.timeline) + [{"event": event, "timestamp": _now()}]

    await _with_task(tenant_id, task_id, mutate)


async def fail_task(
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
    error: dict,
    event: str = "Failed",
) -> None:
    """Mark a task Failed with an error payload."""

    def mutate(task: BackgroundTask) -> None:
        task.status = TaskStatus.FAILED.value
        task.error = error
        task.completed_at = datetime.now(timezone.utc)
        task.timeline = list(task.timeline) + [{"event": event, "timestamp": _now()}]

    await _with_task(tenant_id, task_id, mutate)

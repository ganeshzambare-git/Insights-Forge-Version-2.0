"""
Insight Forge V2 — Background Task Service.

Request-time reads and creation of background job records. The actual progress
updates happen in ``app.workers.task_runner`` (own session, run from FastAPI
BackgroundTasks) — no Celery/Redis involved.
"""

import uuid
from datetime import datetime, timezone
from typing import Sequence

from app.core.enums import TaskStatus
from app.models.background_task import BackgroundTask
from app.repositories.background_task import BackgroundTaskRepository
from app.services.audit import AuditLoggerProtocol
from app.services.base import BaseService
from app.services.context import ServiceContext
from app.services.providers import ClockProvider, UUIDProvider
from app.services.result import ServiceResult
from app.services.uow import UnitOfWork


class TaskService(BaseService):
    """Business service governing background task records."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = BackgroundTaskRepository(session=uow.session)

    async def create_task(
        self, tenant_id: uuid.UUID, task_type: str
    ) -> ServiceResult[BackgroundTask]:
        """Register a new background task in the Pending state."""

        async def action() -> BackgroundTask:
            now = datetime.now(timezone.utc).isoformat()
            task = BackgroundTask(
                task_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                task_type=task_type,
                status=TaskStatus.PENDING.value,
                progress_pct=0,
                timeline=[{"event": "Queued", "timestamp": now}],
            )
            return await self.repo.create(task)

        return await self.execute_command(
            "create_task", action, success_msg="Task queued successfully."
        )

    async def get_task(self, task_id: uuid.UUID) -> BackgroundTask | None:
        """Fetch a single background task by ID."""
        return await self.repo.get_by_id(task_id)

    async def list_tasks(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[BackgroundTask]:
        """List a tenant's background tasks, newest first."""
        return await self.repo.list_for_tenant(tenant_id, limit=limit, offset=offset)

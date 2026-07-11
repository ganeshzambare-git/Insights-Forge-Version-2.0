"""
Insight Forge V2 — Background Task Repository.

Data access for background job lifecycle records (tenant-scoped via RLS).
"""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_task import BackgroundTask
from app.repositories.base import BaseRepository


class BackgroundTaskRepository(BaseRepository[BackgroundTask]):
    """Repository managing data operations for the BackgroundTask entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=BackgroundTask, session=session)

    async def list_for_tenant(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[BackgroundTask]:
        """Fetch a tenant's background tasks, newest first."""
        return await self.get_all(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            order_by=BackgroundTask.created_at.desc(),
        )

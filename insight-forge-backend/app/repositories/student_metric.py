"""
Insight Forge V2 — Student Metric Repository.

Handles querying academic and attendance analytics records.
"""

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student_metric import StudentMetric
from app.repositories.base import BaseRepository


class StudentMetricRepository(BaseRepository[StudentMetric]):
    """Repository managing data operations for the StudentMetric entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the student metric repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=StudentMetric, session=session)

    async def get_by_student(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> Sequence[StudentMetric]:
        """Fetch all academic metric records for a specific student user.

        Args:
            tenant_id: The UUID of the tenant scope.
            student_id: The UUID of the student user.

        Returns:
            A sequence of StudentMetric records.
        """
        return await self.get_all(tenant_id=tenant_id, student_user_id=student_id)

    async def get_latest_metrics(
        self, tenant_id: uuid.UUID, limit: int = 100
    ) -> Sequence[StudentMetric]:
        """Fetch the latest student metrics within a tenant, ordered by primary key descending.

        Args:
            tenant_id: The UUID of the tenant scope.
            limit: Maximum number of metric records to return.

        Returns:
            A sequence of StudentMetric records.
        """
        return await self.get_all(
            limit=limit,
            order_by=StudentMetric.metric_id.desc(),
            tenant_id=tenant_id,
        )

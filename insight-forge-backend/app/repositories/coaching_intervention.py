"""
Insight Forge V2 — Coaching Intervention Repository.

Handles querying recorded coaching and advisory interventions.
"""

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coaching_intervention import CoachingIntervention
from app.repositories.base import BaseRepository


class CoachingInterventionRepository(BaseRepository[CoachingIntervention]):
    """Repository managing data operations for the CoachingIntervention entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the coaching intervention repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=CoachingIntervention, session=session)

    async def get_by_student(
        self, tenant_id: uuid.UUID, student_id: uuid.UUID
    ) -> Sequence[CoachingIntervention]:
        """Fetch all intervention records logged for a specific student user.

        Args:
            tenant_id: The UUID of the tenant scope.
            student_id: The UUID of the student user.

        Returns:
            A sequence of CoachingIntervention records.
        """
        return await self.get_all(tenant_id=tenant_id, student_user_id=student_id)

    async def get_recent_interventions(
        self, tenant_id: uuid.UUID, limit: int = 50
    ) -> Sequence[CoachingIntervention]:
        """Fetch the most recent interventions within a tenant, ordered by recorded timestamp descending.

        Args:
            tenant_id: The UUID of the tenant scope.
            limit: Maximum number of intervention records to return.

        Returns:
            A sequence of CoachingIntervention records.
        """
        return await self.get_all(
            limit=limit,
            order_by=CoachingIntervention.recorded_timestamp.desc(),
            tenant_id=tenant_id,
        )

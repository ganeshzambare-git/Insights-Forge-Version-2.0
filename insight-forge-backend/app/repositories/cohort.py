"""
Insight Forge V2 — Cohort Repository.

Handles cohort group queries.
"""

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cohort import Cohort
from app.repositories.base import BaseRepository


class CohortRepository(BaseRepository[Cohort]):
    """Repository managing data operations for the Cohort entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the cohort repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=Cohort, session=session)

    async def get_by_code(self, tenant_id: uuid.UUID, code: str) -> Cohort | None:
        """Retrieve a cohort by its tenant and unique code identifier.

        Args:
            tenant_id: The UUID of the tenant scope.
            code: The cohort code string.

        Returns:
            The Cohort record if found, else None.
        """
        return await self.get_one_or_none(tenant_id=tenant_id, cohort_code=code)

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> Sequence[Cohort]:
        """Fetch all cohorts belonging to a specific tenant.

        Args:
            tenant_id: The UUID of the tenant scope.

        Returns:
            A sequence of Cohort records.
        """
        return await self.get_all(tenant_id=tenant_id)

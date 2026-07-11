"""
Insight Forge V2 — Budget Allocation Repository.

Data access for tenant budget allocations (tenant-scoped via RLS).
"""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget_allocation import BudgetAllocation
from app.repositories.base import BaseRepository


class BudgetAllocationRepository(BaseRepository[BudgetAllocation]):
    """Repository managing data operations for the BudgetAllocation entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=BudgetAllocation, session=session)

    async def list_for_tenant(
        self, tenant_id: uuid.UUID, dimension: str | None = None
    ) -> Sequence[BudgetAllocation]:
        """Fetch a tenant's budget allocations, optionally filtered by dimension."""
        filters: dict = {"tenant_id": tenant_id}
        if dimension:
            filters["dimension"] = dimension
        return await self.get_all(
            limit=500,
            order_by=BudgetAllocation.category.asc(),
            **filters,
        )

"""
Insight Forge V2 — Dataset Repository.

Handles data-access operations for uploaded datasets. Tenant scoping is
enforced by PostgreSQL RLS; explicit tenant filters are defense-in-depth.
"""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Repository managing data operations for the Dataset entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the dataset repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=Dataset, session=session)

    async def get_by_tenant(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[Dataset]:
        """Fetch datasets for a tenant, newest first.

        Args:
            tenant_id: The UUID of the tenant scope.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            A sequence of Dataset records ordered by creation time (descending).
        """
        return await self.get_all(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            order_by=Dataset.created_at.desc(),
        )

    async def paginate_by_tenant(
        self, tenant_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Dataset], int]:
        """Fetch a paginated page of a tenant's datasets plus the total count.

        Args:
            tenant_id: The UUID of the tenant scope.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            A tuple of (datasets page, total matching count).
        """
        return await self.paginate(
            limit=limit,
            offset=offset,
            order_by=Dataset.created_at.desc(),
            tenant_id=tenant_id,
        )

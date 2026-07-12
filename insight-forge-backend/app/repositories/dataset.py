"""
Insight Forge V2 — Dataset Repositories.

Data access for uploaded datasets and their generically-stored JSONB rows.
"""

import uuid
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, DatasetRecord
from app.repositories.base import BaseRepository
from app.repositories.exceptions import RepositoryError


class DatasetRepository(BaseRepository[Dataset]):
    """Repository managing data operations for the Dataset entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Dataset, session=session)

    async def list_by_tenant(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[Dataset]:
        """Return datasets for a tenant, newest first."""
        try:
            stmt = (
                select(Dataset)
                .where(Dataset.tenant_id == tenant_id)
                .order_by(Dataset.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during list_by_tenant: {str(e)}") from e


class DatasetRecordRepository(BaseRepository[DatasetRecord]):
    """Repository managing data operations for stored dataset rows."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=DatasetRecord, session=session)

    async def bulk_add(self, records: list[DatasetRecord]) -> None:
        """Insert many dataset rows in a single flush."""
        try:
            self.session.add_all(records)
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during bulk_add: {str(e)}") from e

    async def list_by_dataset(
        self, dataset_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[DatasetRecord]:
        """Return the stored rows of a dataset in original order."""
        try:
            stmt = (
                select(DatasetRecord)
                .where(DatasetRecord.dataset_id == dataset_id)
                .order_by(DatasetRecord.row_index.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during list_by_dataset: {str(e)}") from e

    async def all_payloads(self, dataset_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return every stored row payload for a dataset, ordered by row index."""
        try:
            stmt = (
                select(DatasetRecord.payload)
                .where(DatasetRecord.dataset_id == dataset_id)
                .order_by(DatasetRecord.row_index.asc())
            )
            result = await self.session.execute(stmt)
            return [row for row in result.scalars().all()]
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during all_payloads: {str(e)}") from e

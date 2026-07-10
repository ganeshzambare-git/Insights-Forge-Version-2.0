"""
Insight Forge V2 — Generic Async Repository.

Provides reusable data access operations using SQLAlchemy 2.0 style queries.
"""

from typing import Any, Generic, Sequence, TypeVar
from sqlalchemy import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.exceptions import RepositoryError

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic repository providing asynchronous database operations for an ORM model."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            model: The SQLAlchemy ORM model class.
            session: Injected AsyncSession database session.
        """
        self.model = model
        self.session = session

    async def create(self, entity: ModelType) -> ModelType:
        """Add a new record to the session.

        Args:
            entity: The ORM model instance to add.

        Returns:
            The added ORM model instance.
        """
        try:
            self.session.add(entity)
            return entity
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during create: {str(e)}") from e

    async def get_by_id(self, id_: Any) -> ModelType | None:
        """Fetch a single record by its primary key.

        Args:
            id_: The primary key value.

        Returns:
            The ORM model instance if found, else None.
        """
        try:
            return await self.session.get(self.model, id_)
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during get_by_id: {str(e)}") from e

    async def get_one_or_none(self, **filters: Any) -> ModelType | None:
        """Fetch a single record matching specific keyword filters.

        Args:
            **filters: Field-value pairs to filter by.

        Returns:
            The matching ORM model instance, or None.
        """
        try:
            stmt = select(self.model).filter_by(**filters)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Database error during get_one_or_none: {str(e)}"
            ) from e

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: Any = None,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Fetch a sequence of records matching optional filters with limit and offset.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            order_by: Sorting field or expression.
            **filters: Field-value pairs to filter by.

        Returns:
            A sequence of ORM model instances.
        """
        try:
            stmt = select(self.model).filter_by(**filters)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during get_all: {str(e)}") from e

    async def paginate(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: Any = None,
        **filters: Any,
    ) -> tuple[Sequence[ModelType], int]:
        """Fetch a paginated subset of records and the total matching count.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            order_by: Sorting field or expression.
            **filters: Field-value pairs to filter by.

        Returns:
            A tuple of (matching records, total count).
        """
        try:
            # Query count
            count_stmt = (
                select(func.count()).select_from(self.model).filter_by(**filters)
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar_or_none() or 0

            # Query page records
            stmt = select(self.model).filter_by(**filters)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            records = result.scalars().all()

            return records, total
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during paginate: {str(e)}") from e

    async def update(self, entity: ModelType, **updates: Any) -> ModelType:
        """Update fields of an ORM entity and return it.

        Args:
            entity: The ORM model instance to update.
            **updates: Keyword arguments of field-value pairs to update on the entity.

        Returns:
            The updated ORM model instance.
        """
        try:
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            return entity
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during update: {str(e)}") from e

    async def delete(self, entity: ModelType) -> None:
        """Remove a record from the database session.

        Args:
            entity: The ORM model instance to delete.
        """
        try:
            await self.session.delete(entity)
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during delete: {str(e)}") from e

    async def exists(self, **filters: Any) -> bool:
        """Check if a record matching specific filters exists using efficient EXISTS select.

        Args:
            **filters: Field-value pairs to check existence by.

        Returns:
            True if matching record exists, else False.
        """
        try:
            conditions = [getattr(self.model, k) == v for k, v in filters.items()]
            stmt = (
                select(exists().where(*conditions)) if conditions else select(exists())
            )
            result = await self.session.execute(stmt)
            return bool(result.scalar())
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during exists: {str(e)}") from e

    async def count(self, **filters: Any) -> int:
        """Get the total count of records matching specific filters.

        Args:
            **filters: Field-value pairs to count.

        Returns:
            The total count of matching records.
        """
        try:
            stmt = select(func.count()).select_from(self.model).filter_by(**filters)
            result = await self.session.execute(stmt)
            return result.scalar_or_none() or 0
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during count: {str(e)}") from e

    async def flush(self) -> None:
        """Flush changes in the current session to the database."""
        try:
            await self.session.flush()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during flush: {str(e)}") from e

    async def refresh(self, entity: ModelType) -> None:
        """Refresh the attributes of an instance from the database.

        Args:
            entity: The ORM model instance to refresh.
        """
        try:
            await self.session.refresh(entity)
        except SQLAlchemyError as e:
            raise RepositoryError(f"Database error during refresh: {str(e)}") from e

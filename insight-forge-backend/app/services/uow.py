"""
Insight Forge V2 — Unit of Work.

Encapsulates transaction boundaries, supporting nested operations without double commits.
"""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Orchestrates database transaction blocks and tracks scope nesting depth."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the Unit of Work.

        Args:
            session: The active SQLAlchemy AsyncSession.
        """
        self.session = session
        self._depth = 0
        self._failed = False

    async def __aenter__(self) -> "UnitOfWork":
        """Enter a new transaction boundary block."""
        self._depth += 1
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the transaction boundary block, committing on success or rolling back on failure."""
        self._depth -= 1
        if exc_type is not None:
            self._failed = True
            await self.rollback()
        elif self._depth == 0 and not self._failed:
            await self.commit()

    async def commit(self) -> None:
        """Commit the active database session transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the active database session transaction."""
        await self.session.rollback()

    async def flush(self) -> None:
        """Flush current transaction memory changes to the database."""
        await self.session.flush()

    async def refresh(self, entity: Any) -> None:
        """Refresh ORM instance attributes from the database."""
        await self.session.refresh(entity)

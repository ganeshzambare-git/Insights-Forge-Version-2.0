"""
Insight Forge V2 — Session Repository.

Handles persistent authentication session queries.
"""

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository managing data operations for the Session entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the session repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=Session, session=session)

    async def get_by_jti(self, jti: str) -> Session | None:
        """Retrieve a session by its unique JWT token JTI (JSON Web Token ID).

        Args:
            jti: Unique JTI claim string.

        Returns:
            The Session record if found, else None.
        """
        return await self.get_one_or_none(jwt_jti=jti)

    async def get_recent_sessions(
        self, tenant_id: uuid.UUID, limit: int = 10
    ) -> Sequence[Session]:
        """Fetch the most recent sessions within a tenant, ordered by expiration date.

        Args:
            tenant_id: The UUID of the tenant scope.
            limit: Maximum number of session records to return.

        Returns:
            A sequence of Session records.
        """
        return await self.get_all(
            limit=limit,
            order_by=Session.expires_at.desc(),
            tenant_id=tenant_id,
        )

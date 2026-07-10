"""
Insight Forge V2 — User Repository.

Handles user storage access and lookup helpers.
"""

import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository managing data operations for the User entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the user repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=User, session=session)

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a User by their corporate email.

        Args:
            email: The corporate email string.

        Returns:
            The User record if found, else None.
        """
        return await self.get_one_or_none(corporate_email=email)

    async def email_exists(self, email: str) -> bool:
        """Check if an email is registered in the system.

        Args:
            email: The email address to check.

        Returns:
            True if registered, otherwise False.
        """
        return await self.exists(corporate_email=email)

    async def list_by_role(
        self, role: str, tenant_id: uuid.UUID | None = None
    ) -> Sequence[User]:
        """Fetch all users assigned to a specific role, optionally filtered by tenant.

        Args:
            role: The role to filter by (e.g. 'Admin', 'Student').
            tenant_id: Optional UUID of the tenant to scope users.

        Returns:
            A sequence of matching User instances.
        """
        filters = {"assigned_role": role}
        if tenant_id is not None:
            filters["tenant_id"] = tenant_id
        return await self.get_all(**filters)

"""
Insight Forge V2 — Tenant Repository.

Handles institutional data partitioning operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository managing data operations for the Tenant entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the tenant repository.

        Args:
            session: Injected AsyncSession database session.
        """
        super().__init__(model=Tenant, session=session)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Retrieve a Tenant by its unique URL slug.

        Args:
            slug: The unique string identifier.

        Returns:
            The Tenant record if found, else None.
        """
        return await self.get_one_or_none(tenant_slug=slug)

    async def slug_exists(self, slug: str) -> bool:
        """Check if a tenant slug is already registered.

        Args:
            slug: The URL slug to verify.

        Returns:
            True if the slug exists, otherwise False.
        """
        return await self.exists(tenant_slug=slug)

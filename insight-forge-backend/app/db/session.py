"""
Insight Forge V2 — Database Sessions.

Manages connection sessions using SQLAlchemy async context handlers.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import engine
from app.middleware.tenant import tenant_context

# Define the global async session creator
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions.

    Yields:
        An active AsyncSession instances that auto-closes.
    """
    async with async_session_maker() as session:
        tenant_id = tenant_context.get()
        if tenant_id:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )
        try:
            yield session
        finally:
            await session.close()

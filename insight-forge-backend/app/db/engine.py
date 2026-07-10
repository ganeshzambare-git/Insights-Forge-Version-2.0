"""
Insight Forge V2 — Database Engine.

Configures the SQLAlchemy asynchronous engine utilizing psycopg3.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# Create async engine with connection pooling settings
engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    future=True,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

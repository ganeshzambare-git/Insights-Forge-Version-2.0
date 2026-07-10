"""
Insight Forge V2 — Database Health Utility.

Executes check queries asynchronously against Neon to verify connection state and measure latency.
"""

from __future__ import annotations

import time
import logging
from typing import Any

from sqlalchemy import text

from app.db.engine import engine

logger = logging.getLogger("app.db.health")


async def check_database_health() -> dict[str, Any]:
    """Verify database connection, execute a ping query, and calculate round-trip latency.

    Returns:
        A structured dictionary describing database status, latency, and errors.
    """
    start_time = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "error": None,
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error("Database connection check failed: %s", str(e), exc_info=True)
        return {
            "status": "down",
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
        }

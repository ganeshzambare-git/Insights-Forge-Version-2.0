"""
Insight Forge V2 — Application Lifespan.

Orchestrates startup verification (logging setup, db connection check) and shutdown resource disposal.
"""

from datetime import datetime, timezone
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.engine import engine
from app.db.health import check_database_health

logger = logging.getLogger("app.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI async context manager lifespan for startup and shutdown execution hooks.

    Args:
        app: The running FastAPI instance.
    """
    # 1. Initialize logging
    setup_logging(settings.LOG_LEVEL)
    logger.info("Initializing Insight Forge V2 application startup sequence...")

    # Record startup timestamp using UTC timezone-aware datetime
    app.state.startup_time = datetime.now(timezone.utc)

    # Validate configuration and log database connection pool settings
    try:
        pool_size = settings.DB_POOL_SIZE
        max_overflow = settings.DB_MAX_OVERFLOW
        pool_timeout = settings.DB_POOL_TIMEOUT
        pool_recycle = settings.DB_POOL_RECYCLE
        logger.info(
            "Database connection pool configured - pool_size: %d, max_overflow: %d, pool_timeout: %ds, pool_recycle: %ds",
            pool_size,
            max_overflow,
            pool_timeout,
            pool_recycle,
        )
    except ValidationError as e:
        logger.critical(
            "[Configuration Error] Application configuration validation failed. Stage: startup_config_verification. Exception: ValidationError. Reason: %s",
            str(e),
        )
        raise

    # 2. Verify database connection
    logger.info("Verifying database connection connectivity...")
    try:
        db_result = await check_database_health()
        if db_result["status"] == "down":
            logger.error(
                "[Database Error] Database connectivity check failed. Stage: startup_db_verification. "
                "Reason: %s. Exception: InterfaceError/ConnectionError. "
                "Recommendation: Verify Neon database credentials, check system firewall/routing rules, or verify DB status. "
                "Application starting in degraded mode.",
                db_result["error"],
            )
        else:
            logger.info(
                "Database connectivity check succeeded. Latency: %sms",
                db_result["latency_ms"],
            )
    except Exception as e:
        logger.critical(
            "[Unexpected Error] An unexpected error occurred during database health check. "
            "Stage: startup_db_verification. Exception: %s. Reason: %s",
            type(e).__name__,
            str(e),
        )

    # 3. Initialize application state
    app.state.db_engine = engine

    logger.info("Insight Forge V2 application startup sequence completed successfully.")

    yield

    # 4. Shutdown and cleanup
    logger.info("Initiating Insight Forge V2 application shutdown sequence...")

    # Dispose of the connection pool with verification
    logger.info("Closing database connection pool...")
    try:
        await engine.dispose()
        logger.info("Database engine disposed successfully.")
    except Exception as e:
        logger.warning(
            "[Application Error] Failed to dispose of the database connection pool cleanly. "
            "Exception: %s. Reason: %s",
            type(e).__name__,
            str(e),
        )

    logger.info(
        "Insight Forge V2 application shutdown sequence completed successfully."
    )

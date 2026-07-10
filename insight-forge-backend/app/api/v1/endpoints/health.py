"""
Insight Forge V2 — V1 Health Check Endpoint.

Exposes REST endpoint for diagnostic, liveness, and readiness metrics.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, Response, status

from app.core.config import settings
from app.db.health import check_database_health

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_health(request: Request, response: Response) -> dict[str, Any]:
    """Perform a system health check.

    Returns:
        A dictionary containing health diagnostic and system performance metrics.
    """
    # Protect against cache headers
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    db_result = await check_database_health()
    db_ok = db_result["status"] == "up"

    # Calculate uptime
    startup_time = getattr(request.app.state, "startup_time", None)
    if startup_time:
        uptime_seconds = int(
            (datetime.now(timezone.utc) - startup_time).total_seconds()
        )
    else:
        uptime_seconds = 0

    overall_status = "healthy" if db_ok else "degraded"

    database_detail = {
        "status": db_result["status"],
        "latency_ms": db_result["latency_ms"],
    }
    if db_result.get("error"):
        database_detail["error"] = db_result["error"]

    payload = {
        "status": overall_status,
        "api_version": "v2",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "readiness": db_ok,
        "liveness": True,
        "application": {
            "name": settings.APP_NAME,
            "api_version": "v2",
            "environment": settings.ENVIRONMENT,
        },
        "build": {
            "version": settings.VERSION,
            "commit": None,
            "build_time": None,
        },
        "dependencies": {
            "database": database_detail,
            "redis": {"status": "pending"},
            "workers": {"status": "pending"},
        },
    }

    # Backward-compatible representation
    payload["services"] = {
        "database": db_result,
    }

    return payload

"""
Insight Forge V2 — FastAPI Main Entrypoint.

Instantiates the FastAPI application, registers global exception handlers,
configures CORS/GZip/TrustedHost middlewares, and loads API routes.
"""

from __future__ import annotations

import asyncio
import sys

# Set selector event loop on Windows to support psycopg async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import ApplicationException
from app.db.health import check_database_health
from app.lifespan import lifespan
from app.api.v1.router import api_router

# Service exceptions & middlewares
from app.services.exceptions import (
    ServiceError,
    ValidationError as ServiceValidationError,
    ConflictError as ServiceConflictError,
    NotFoundError as ServiceNotFoundError,
    AuthenticationError as ServiceAuthenticationError,
    AuthorizationError as ServiceAuthorizationError,
    BusinessRuleViolation as ServiceBusinessRuleViolation,
)
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.timing import TimingMiddleware
from app.middleware.tenant import TenantMiddleware
from app.utils.response import api_response

logger = logging.getLogger("app.main")

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIST = BACKEND_DIR.parent / "insight-forge-frontend" / "out"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

# Initialize the main FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade multi-tenant educational intelligence platform.",
    version=settings.VERSION,
    lifespan=lifespan,
)

# ============================================================
# MIDDLEWARE REGISTRATION
# ============================================================

# 1. TrustedHostMiddleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# 2. CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. GZipMiddleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)

# 4. RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# 5. SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# 6. TimingMiddleware
app.add_middleware(TimingMiddleware)

# 7. TenantMiddleware
app.add_middleware(TenantMiddleware)

# ============================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================


@app.exception_handler(ServiceAuthenticationError)
async def service_auth_exception_handler(
    request: Request, exc: ServiceAuthenticationError
) -> JSONResponse:
    """Handle service layer authentication failures (401)."""
    logger.warning("AuthenticationError on path %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ServiceAuthorizationError)
async def service_authz_exception_handler(
    request: Request, exc: ServiceAuthorizationError
) -> JSONResponse:
    """Handle service layer role authorization/RBAC failures (403)."""
    logger.warning("AuthorizationError on path %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ServiceNotFoundError)
async def service_not_found_exception_handler(
    request: Request, exc: ServiceNotFoundError
) -> JSONResponse:
    """Handle service layer missing resource exceptions (404)."""
    logger.info("NotFoundError on path %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ServiceConflictError)
async def service_conflict_exception_handler(
    request: Request, exc: ServiceConflictError
) -> JSONResponse:
    """Handle service layer unique duplicate conflicts (409)."""
    logger.info("ConflictError on path %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ServiceValidationError)
async def service_validation_exception_handler(
    request: Request, exc: ServiceValidationError
) -> JSONResponse:
    """Handle service layer input syntax/validation issues (422)."""
    logger.info("ValidationError on path %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ServiceBusinessRuleViolation)
async def service_business_rule_exception_handler(
    request: Request, exc: ServiceBusinessRuleViolation
) -> JSONResponse:
    """Handle service layer academic policy violations (400)."""
    logger.warning(
        "BusinessRuleViolation on path %s: %s", request.url.path, exc.message
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ServiceError)
async def service_generic_exception_handler(
    request: Request, exc: ServiceError
) -> JSONResponse:
    """Handle generic unclassified service layer errors (400)."""
    logger.error("ServiceError on path %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.error_code, "message": exc.message}],
        ),
    )


@app.exception_handler(ApplicationException)
async def application_exception_handler(
    request: Request, exc: ApplicationException
) -> JSONResponse:
    """Handle custom legacy application exceptions."""
    logger.error(
        "ApplicationException caught: %s - status: %d", exc.message, exc.status_code
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=api_response(
            success=False,
            message=exc.message,
            errors=[{"error": exc.__class__.__name__, "message": exc.message}],
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle input request schema validation failures (422)."""
    logger.warning(
        "RequestValidationError on path %s: %s", request.url.path, str(exc.errors())
    )
    formatted_errors = [
        {
            "field": ".".join(map(str, error["loc"])),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=api_response(
            success=False,
            message="Input validation failed.",
            errors=formatted_errors,
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard Starlette/FastAPI HTTPExceptions."""
    logger.warning(
        "HTTPException on path %s: %s - status: %d",
        request.url.path,
        exc.detail,
        exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=api_response(
            success=False,
            message=exc.detail,
            errors=[{"error": "http_error", "message": exc.detail}],
        ),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled internal backend exceptions (500)."""
    logger.critical(
        "Unhandled Exception caught on path %s: %s",
        request.url.path,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=api_response(
            success=False,
            message="An unexpected error occurred. Please contact system support.",
            errors=[{"error": "InternalServerError", "message": str(exc)}],
        ),
    )


# ============================================================
# ROUTER REGISTRATION & ROOT ENDPOINTS
# ============================================================


@app.get("/", status_code=status.HTTP_200_OK, response_model=None)
async def root() -> FileResponse | dict[str, str]:
    """Serve the frontend shell when available, otherwise return API metadata."""
    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX)

    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "message": "Insight Forge V2 Backend Application Foundation is Online.",
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_root_health(request: Request, response: Response) -> dict[str, Any]:
    """Perform system health diagnostics."""
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


# Register the primary consolidated API router under /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

if (FRONTEND_DIST / "_next").is_dir():
    app.mount(
        "/_next",
        StaticFiles(directory=FRONTEND_DIST / "_next"),
        name="next-static",
    )


def _frontend_file_for_path(path: str) -> Path | None:
    """Resolve a static-export frontend path without escaping the export directory."""
    candidates = [
        FRONTEND_DIST / path,
        FRONTEND_DIST / f"{path}.html",
        FRONTEND_DIST / path / "index.html",
    ]

    dist_root = FRONTEND_DIST.resolve()
    for candidate in candidates:
        resolved = candidate.resolve()
        if dist_root in resolved.parents or resolved == dist_root:
            if resolved.is_file():
                return resolved
    return None


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def serve_frontend(full_path: str) -> FileResponse:
    """Serve exported frontend routes from the same Uvicorn process."""
    if full_path.startswith("api/"):
        raise StarletteHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    if not FRONTEND_INDEX.is_file():
        raise StarletteHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frontend build not found. Run `npm run build` in insight-forge-frontend.",
        )

    frontend_file = _frontend_file_for_path(full_path)
    if frontend_file:
        return FileResponse(frontend_file)

    return FileResponse(FRONTEND_INDEX)


# This application is intentionally structured to support future integration of:
# - Redis
# - Background Workers
# - WebSockets
# - OpenTelemetry
# - Prometheus Metrics
# - Request Correlation Middleware

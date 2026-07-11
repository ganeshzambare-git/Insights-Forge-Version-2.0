"""
Insight Forge V2 — Timing Middleware.

Implements latency tracking and appends the X-Response-Time header to all HTTP responses.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.runtime_metrics import runtime_metrics
from app.middleware.tenant import tenant_context


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to measure latency and feed real runtime throughput metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000  # ms
        response.headers["X-Response-Time"] = f"{process_time:.2f}ms"

        # Record real throughput for observability (best-effort tenant label).
        tenant_id = tenant_context.get()
        tenant_label = str(tenant_id) if tenant_id else (
            request.headers.get("X-Tenant-ID") or "anonymous"
        )
        runtime_metrics.record_request(tenant_label)
        return response

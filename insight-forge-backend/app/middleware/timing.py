"""
Insight Forge V2 — Timing Middleware.

Implements latency tracking and appends the X-Response-Time header to all HTTP responses.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to measure and inject HTTP response latency headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000  # ms
        response.headers["X-Response-Time"] = f"{process_time:.2f}ms"
        return response

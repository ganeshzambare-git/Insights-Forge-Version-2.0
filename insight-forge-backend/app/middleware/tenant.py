"""
Insight Forge V2 — Tenant Middleware.

Captures the active tenant ID from headers or JWT tokens and propagates it using ContextVar.
"""

from contextvars import ContextVar
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# ContextVar to hold the tenant_id for the current request context
tenant_context: ContextVar[uuid.UUID | None] = ContextVar("tenant_context", default=None)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to parse tenant context from request headers or JWT tokens."""

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id_str = request.headers.get("X-Tenant-ID")
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        tenant_id = None
        if tenant_id_str:
            try:
                tenant_id = uuid.UUID(tenant_id_str)
            except ValueError:
                pass

        if not tenant_id and token:
            try:
                from app.core.security import decode_token
                payload = decode_token(token)
                jwt_tenant_id = payload.get("tenant_id")
                if jwt_tenant_id:
                    tenant_id = uuid.UUID(jwt_tenant_id)
            except Exception:
                pass

        # Set tenant ID in context variable
        token_ctx = tenant_context.set(tenant_id)
        try:
            response = await call_next(request)
            return response
        finally:
            tenant_context.reset(token_ctx)

"""
Insight Forge V2 — Service Context.

Defines the request execution context carrying tenant identity and tracing metadata.
"""

from dataclasses import dataclass
import uuid


@dataclass(frozen=True, slots=True)
class ServiceContext:
    """Immutable execution context for tracing and isolating service calls."""

    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    role: str | None = None
    request_id: str | None = None

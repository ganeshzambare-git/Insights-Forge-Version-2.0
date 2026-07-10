"""
Insight Forge V2 — Service Response Envelopes.

Defines standardized data structures for service commands and pagination.
"""

from dataclasses import dataclass, field
from typing import Any, Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class ServiceResult(Generic[T]):
    """Standardized response envelope returned by service mutations (commands)."""

    success: bool
    data: T | None = None
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PaginationParams:
    """Standardized offset-based pagination criteria input parameters."""

    limit: int = 20
    offset: int = 0


@dataclass(frozen=True, slots=True)
class PaginationResult(Generic[T]):
    """Envelopes search lists along with row counts for API-side serialization."""

    items: Sequence[T]
    total: int
    limit: int
    offset: int

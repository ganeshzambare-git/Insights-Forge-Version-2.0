"""
Insight Forge V2 — Infrastructure Providers.

Declares protocols and default implementations for Clock and UUID services to enable test mocks.
"""

from datetime import datetime, timezone
from typing import Protocol
import uuid


class ClockProvider(Protocol):
    """Protocol defining temporal provider operations."""

    def now(self) -> datetime:
        """Return the current timezone-aware UTC datetime.

        Returns:
            A timezone-aware datetime instance in UTC.
        """
        ...


class UUIDProvider(Protocol):
    """Protocol defining unique identifier generation operations."""

    def generate(self) -> uuid.UUID:
        """Generate a random UUID.

        Returns:
            A randomly generated UUID instance.
        """
        ...


class SystemClockProvider:
    """Standard system clock returning timezone-aware UTC times."""

    def now(self) -> datetime:
        """Return timezone-aware UTC current time."""
        return datetime.now(timezone.utc)


class SystemUUIDProvider:
    """Standard system random identifier generator using uuid4."""

    def generate(self) -> uuid.UUID:
        """Generate a random UUID4."""
        return uuid.uuid4()

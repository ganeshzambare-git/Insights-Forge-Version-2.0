"""
Insight Forge V2 — Pytest Shared Fixtures.

Defines global fixtures for database sessions, mocking, and app configuration.
"""

import asyncio
from collections.abc import Generator
import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a persistent session-scoped asyncio event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

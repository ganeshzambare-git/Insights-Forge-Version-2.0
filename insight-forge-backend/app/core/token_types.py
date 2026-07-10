"""
Insight Forge V2 — Token Types.

Defines the string enumeration for token classification (access vs refresh).
"""

from enum import StrEnum


class TokenType(StrEnum):
    """Enumeration of supported JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"

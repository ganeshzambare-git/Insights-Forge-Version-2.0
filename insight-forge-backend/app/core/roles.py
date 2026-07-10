"""
Insight Forge V2 — User Roles.

Defines the string enumeration for user permission levels.
"""

from enum import StrEnum


class Role(StrEnum):
    """User authorization roles matching the database constraint definitions."""

    ADMIN = "Admin"
    DEAN = "Dean"
    FACULTY = "Faculty"
    STUDENT = "Student"

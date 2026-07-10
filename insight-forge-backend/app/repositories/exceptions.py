"""
Insight Forge V2 — Repository Layer Exceptions.

Defines non-HTTP exceptions raised during database operations.
"""


class RepositoryError(Exception):
    """Base exception for all repository layer errors."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when a requested database entity is not found."""

    pass


class DuplicateEntryError(RepositoryError):
    """Raised when an operation violates a unique constraint in the database."""

    pass

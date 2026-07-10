"""
Insight Forge V2 — Reusable Application Exceptions.

Defines custom exception classes mapped to HTTP status codes for structured error reporting.
"""

from __future__ import annotations

from typing import Any


class ApplicationException(Exception):
    """Base exception for all application-specific errors."""

    def __init__(
        self, message: str, status_code: int = 500, details: Any = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class AuthenticationException(ApplicationException):
    """Raised when authentication verification fails."""

    def __init__(
        self, message: str = "Could not validate credentials", details: Any = None
    ) -> None:
        super().__init__(message, status_code=401, details=details)


class AuthorizationException(ApplicationException):
    """Raised when a user lacks permissions to perform an action."""

    def __init__(self, message: str = "Permission denied", details: Any = None) -> None:
        super().__init__(message, status_code=403, details=details)


class ResourceNotFoundException(ApplicationException):
    """Raised when an expected database record is not found."""

    def __init__(
        self, message: str = "Resource not found", details: Any = None
    ) -> None:
        super().__init__(message, status_code=404, details=details)


class ValidationException(ApplicationException):
    """Raised when data validations or invariants fail."""

    def __init__(
        self, message: str = "Input validation failed", details: Any = None
    ) -> None:
        super().__init__(message, status_code=422, details=details)


class ConflictException(ApplicationException):
    """Raised when an operation conflicts with the current database state."""

    def __init__(self, message: str = "Conflict occurred", details: Any = None) -> None:
        super().__init__(message, status_code=409, details=details)

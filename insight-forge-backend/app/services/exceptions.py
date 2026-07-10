"""
Insight Forge V2 — Service Layer Exceptions.

Defines custom domain exceptions for business validation and error states.
"""


class ServiceError(Exception):
    """Base exception for all service layer errors.

    Includes a machine-readable error code for API response mappings.
    """

    def __init__(self, message: str, error_code: str = "service_error") -> None:
        """Initialize the service error.

        Args:
            message: User-friendly descriptive error message.
            error_code: Machine-readable unique error string.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ValidationError(ServiceError):
    """Raised when input validation or schema integrity checks fail."""

    def __init__(self, message: str, error_code: str = "validation_error") -> None:
        super().__init__(message, error_code)


class ConflictError(ServiceError):
    """Raised when unique database constraints or transaction conflicts occur."""

    def __init__(self, message: str, error_code: str = "conflict_error") -> None:
        super().__init__(message, error_code)


class NotFoundError(ServiceError):
    """Raised when a requested resource or aggregate entity does not exist."""

    def __init__(self, message: str, error_code: str = "not_found") -> None:
        super().__init__(message, error_code)


class AuthenticationError(ServiceError):
    """Raised when token authentication or session validation fails."""

    def __init__(self, message: str, error_code: str = "authentication_error") -> None:
        super().__init__(message, error_code)


class AuthorizationError(ServiceError):
    """Raised when a user lacks privileges or violates tenant isolation boundaries."""

    def __init__(self, message: str, error_code: str = "authorization_error") -> None:
        super().__init__(message, error_code)


class BusinessRuleViolation(ServiceError):
    """Raised when execution violates institutional policies or analytics boundaries."""

    def __init__(
        self, message: str, error_code: str = "business_rule_violation"
    ) -> None:
        super().__init__(message, error_code)

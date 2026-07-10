"""
Insight Forge V2 — Custom AI Exceptions.

Defines custom exception classes for the AI Foundation module.
"""

from app.services.exceptions import ServiceError


class AIError(ServiceError):
    """Base exception for all AI-related errors."""

    def __init__(self, message: str, error_code: str = "ai_error") -> None:
        super().__init__(message, error_code)


class AIValidationError(AIError):
    """Raised when data/schema validation for AI inputs/outputs fails."""

    def __init__(self, message: str, error_code: str = "ai_validation_error") -> None:
        super().__init__(message, error_code)


class EvidenceError(AIError):
    """Raised when evidence verification, validation, or trace assertions fail."""

    def __init__(self, message: str, error_code: str = "evidence_error") -> None:
        super().__init__(message, error_code)


class ConfidenceError(AIError):
    """Raised when confidence score computation or bounds assertions fail."""

    def __init__(self, message: str, error_code: str = "confidence_error") -> None:
        super().__init__(message, error_code)


class ReasoningError(AIError):
    """Raised when logical reasoning constraints or hypothesis validation fails."""

    def __init__(self, message: str, error_code: str = "reasoning_error") -> None:
        super().__init__(message, error_code)


class PromptError(AIError):
    """Raised when prompt rendering, parameter validation, or registration fails."""

    def __init__(self, message: str, error_code: str = "prompt_error") -> None:
        super().__init__(message, error_code)


class LLMError(AIError):
    """Raised when interaction with LLM providers fails."""

    def __init__(self, message: str, error_code: str = "llm_error") -> None:
        super().__init__(message, error_code)


class ExecutionError(AIError):
    """Raised when agent execution flow fails or is interrupted."""

    def __init__(self, message: str, error_code: str = "execution_error") -> None:
        super().__init__(message, error_code)

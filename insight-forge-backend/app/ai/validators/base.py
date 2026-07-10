"""
Insight Forge V2 — AI Validator Base Class.

Defines the base interface class for modular AI framework validation.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAIValidator(ABC):
    """Base class for validation modules that inspect inputs/outputs inside the AI flow.

    Provides a clean pattern for decoupling validation constraints from the agent itself.
    """

    @abstractmethod
    def validate(self, data: Any) -> None:
        """Execute validation checks on the target data.

        Args:
            data: The target data (dictionary, Pydantic model, or raw value) to validate.

        Raises:
            AIValidationError: If any validation checks or invariants fail.
        """
        pass

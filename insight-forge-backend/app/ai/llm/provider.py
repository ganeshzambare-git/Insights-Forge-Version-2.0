"""
Insight Forge V2 — LLM Provider Interface.

Defines the interchangeable interface for backend LLM clients.
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class BaseLLMProvider(ABC):
    """Interchangeable interface for various LLM service backends.

    Ensures prompt engineering and reasoning layers remain detached from
    concrete implementation choices (e.g. OpenAI vs Anthropic vs Gemini).
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        """Call generation completion for a single text prompt.

        Args:
            prompt: User-level main instruction text.
            system_prompt: System directive instructions.
            schema: Optional Pydantic model to enforce structured JSON output format.
            temperature: Sampling temperature for randomness.
            kwargs: Vendor-specific overrides (e.g. top_p, max_tokens).

        Returns:
            The raw text string response, or an instance of Pydantic BaseModel if schema is defined.
        """
        pass

    @abstractmethod
    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        """Call chat completion for a history list of role/content message dicts.

        Args:
            messages: List of dialog messages containing 'role' and 'content' keys.
            schema: Optional Pydantic model to enforce structured JSON output format.
            temperature: Sampling temperature for randomness.
            kwargs: Vendor-specific overrides.

        Returns:
            The raw text string response, or an instance of Pydantic BaseModel if schema is defined.
        """
        pass

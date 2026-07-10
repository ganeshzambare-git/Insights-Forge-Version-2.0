"""
Insight Forge V2 — Centralized Prompt Management.

Defines PromptType, PromptTemplate, and PromptManager structures.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from app.ai.exceptions.custom import PromptError


class PromptType(str, Enum):
    """Classification categorization categories for prompts."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"


class PromptTemplate(BaseModel):
    """Encapsulates template specifications, validation parameters, and type details."""

    name: str = Field(..., description="Unique slug identifying this prompt.")
    version: str = Field(..., description="Semantic version string (e.g. 1.0.0).")
    template_str: str = Field(
        ...,
        description="Raw prompt template using standard curly-brace formatting.",
    )
    prompt_type: PromptType = Field(
        ...,
        description="Prompt scope designation category.",
    )
    required_variables: list[str] = Field(
        default_factory=list,
        description="Parameter names required to compile/render this prompt.",
    )

    def render(self, **variables: Any) -> str:
        """Safely interpolate formatting variables into prompt template string.

        Args:
            variables: Key-value parameters.

        Raises:
            PromptError: If missing required parameters or formatting raises errors.
        """
        for req in self.required_variables:
            if req not in variables:
                raise PromptError(
                    f"Required parameter '{req}' missing from render variables "
                    f"for template '{self.name}' v{self.version}."
                )

        try:
            return self.template_str.format(**variables)
        except Exception as e:
            raise PromptError(
                f"Error formatting prompt template '{self.name}' v{self.version}: {str(e)}"
            )


class PromptManager:
    """Registry maintaining references to versioned prompt template definitions."""

    def __init__(self) -> None:
        self._registry: dict[tuple[str, str], PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        """Register template instance into lookup collection.

        Args:
            template: PromptTemplate model instance.
        """
        key = (template.name, template.version)
        self._registry[key] = template

    def get(self, name: str, version: str) -> PromptTemplate:
        """Retrieve template by registry keys.

        Raises:
            PromptError: If template is missing.
        """
        key = (name, version)
        if key not in self._registry:
            raise PromptError(
                f"Prompt template '{name}' with version '{version}' is not registered."
            )
        return self._registry[key]

    def render(self, name: str, version: str, /, **variables: Any) -> str:
        """Render a template in a single execution call."""
        template = self.get(name, version)
        return template.render(**variables)

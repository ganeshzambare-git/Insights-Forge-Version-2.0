"""
Insight Forge V2 — Deterministic Inference Provider.

A drop-in BaseLLMProvider implementation that performs NO network or model calls.
Instead of prompting an external LLM, it computes the structured responses the
pipeline expects directly from the uploaded dataset using reproducible heuristics
(see app.ai.inference.heuristics). Same data in -> same analysis out.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.ai.agents.data_engineer import DatasetUnderstandingLLMResponse
from app.ai.inference.heuristics import (
    infer_analyst_framing,
    infer_dataset_understanding,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.schemas.analyst import AnalystLLMResponse


class HeuristicInferenceProvider(BaseLLMProvider):
    """Computes agent inputs deterministically from the real dataset.

    The dataset (columns + sample rows) is bound at construction time so the
    schema-typed ``generate`` calls made by the agents resolve to real analysis
    of that specific upload rather than any canned response.
    """

    def __init__(
        self,
        dataset_name: str,
        columns: list[str],
        sample_rows: list[dict[str, Any]],
    ) -> None:
        self.dataset_name = dataset_name
        self.columns = columns
        self.sample_rows = sample_rows

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        """Dispatch to the matching deterministic inference routine by schema."""
        if schema is DatasetUnderstandingLLMResponse:
            return infer_dataset_understanding(
                self.dataset_name, self.columns, self.sample_rows
            )
        if schema is AnalystLLMResponse:
            return infer_analyst_framing(
                self.dataset_name, self.columns, self.sample_rows
            )
        if schema is not None and issubclass(schema, BaseModel):
            # Unknown structured request: return a schema-valid empty instance
            # rather than fabricated content.
            return schema()
        # Free-text requests are not used by the analysis pipeline.
        return ""

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        """Deterministic chat stub — the analysis pipeline does not use chat."""
        if schema is not None and issubclass(schema, BaseModel):
            return schema()
        return ""

"""
Insight Forge V2 — Agent Contracts & Response Schemas.

Defines the base structured response model and Protocol contract for AI agents.
"""

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field
from app.ai.context.model import AIContext
from app.ai.evidence.model import Evidence
from app.ai.schemas.confidence import ConfidenceModel


class AgentContractResponse(BaseModel):
    """Structured response object produced by any conforming AI professional agent."""

    success: bool = Field(
        ...,
        description="Flag indicating execution status success.",
    )
    agent_name: str = Field(
        ...,
        description="Machine name of the professional agent that executed.",
    )
    findings: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-value findings and analytical results.",
    )
    confidence: ConfidenceModel = Field(
        ...,
        description="Calculated confidence evaluation for these findings.",
    )
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="List of supporting evidence objects backing findings.",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of execution or validation errors encountered.",
    )


@runtime_checkable
class AgentContract(Protocol):
    """Type-checkable Protocol specifying expected methods for all AI professionals."""

    async def initialize_context(self, context: AIContext) -> None:
        """Initialize parameters or structure execution space inside the context."""
        ...

    async def execute(
        self, context: AIContext, *args: Any, **kwargs: Any
    ) -> AgentContractResponse:
        """Primary execution block containing reasoning loop or provider orchestration."""
        ...

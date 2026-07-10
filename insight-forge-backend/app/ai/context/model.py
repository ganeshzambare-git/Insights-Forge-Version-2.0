"""
Insight Forge V2 — Shared AI Context.

Defines the immutable shared context passed across the agent pipeline.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.ai.schemas.confidence import ConfidenceModel


class AIContext(BaseModel):
    """Immutable execution context shared among different AI professional agents.

    Uses Pydantic v2 config to enforce frozen state. State transitions
    are made by calling the `evolve()` method, which yields a new context instance.
    """

    model_config = {
        "frozen": True,
        "arbitrary_types_allowed": True,
    }

    tenant_id: str = Field(
        ...,
        description="The identifier of the active tenant workspace.",
    )
    dataset_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata describing the target datasets (e.g. schemas, shape, sources).",
    )
    execution_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="General run metadata (e.g. run ID, triggering event details).",
    )
    execution_timestamps: dict[str, datetime] = Field(
        default_factory=dict,
        description="Audit timestamps mapping agent phases to execution times.",
    )
    previous_outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Consolidated storage of historical execution results indexed by agent key.",
    )
    validation_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Trace validation checks performed during the execution cycle.",
    )
    confidence_history: list[ConfidenceModel] = Field(
        default_factory=list,
        description="Historical confidence estimations mapped during execution.",
    )
    evidence_references: list[str] = Field(
        default_factory=list,
        description="References to external or database-stored evidence elements.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Compilation of minor issues or assumptions encountered.",
    )
    execution_status: str = Field(
        "INITIALIZED",
        description="Current state of the agent run (e.g. INITIALIZED, IN_PROGRESS, COMPLETED, FAILED).",
    )

    def evolve(self, **updates: Any) -> "AIContext":
        """Create a new evolved context copy with modified properties.

        Ensures immutability pattern holds.
        """
        # Pydantic v2 uses model_copy for shallow copying and updating fields
        return self.model_copy(update=updates)

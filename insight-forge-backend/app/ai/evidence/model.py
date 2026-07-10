"""
Insight Forge V2 — Evidence Tracking Model.

Defines schemas for traceable findings and statistical validation evidence.
"""

from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Encapsulates evidence supporting a particular finding or assertion."""

    evidence_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this piece of evidence.",
    )
    source: str = Field(
        ...,
        description="The source of the evidence (e.g. table name, file name, query ID).",
    )
    supporting_columns: list[str] = Field(
        default_factory=list,
        description="List of columns, metrics, or fields supporting this evidence.",
    )
    statistical_support: dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical metadata or calculations supporting the finding.",
    )
    business_support: str = Field(
        ...,
        description="Natural language business context explaining why the evidence is meaningful.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score specifically associated with this piece of evidence.",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Key assumptions made when analyzing or generating this evidence.",
    )
    notes: str = Field(
        "",
        description="Additional context, developer flags, or verification details.",
    )
    validation_status: str = Field(
        "PENDING",
        description="Verification state of this evidence (e.g. PENDING, CONFIRMED, REFUTED).",
    )

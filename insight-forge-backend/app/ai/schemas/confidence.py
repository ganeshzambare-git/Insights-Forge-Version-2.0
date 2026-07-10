"""
Insight Forge V2 — Confidence Model Schema.

Defines the standard schema for confidence metrics returned by AI processes.
"""

from pydantic import BaseModel, Field


class ConfidenceModel(BaseModel):
    """Represents a standardized confidence assessment for AI outputs."""

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The confidence score between 0.0 and 1.0.",
    )
    confidence_level: str = Field(
        ...,
        description="Confidence categorical level (e.g. HIGH, MEDIUM, LOW).",
    )
    explanation: str = Field(
        ...,
        description="Detailed explanation of how the score was calculated.",
    )
    uncertainty: str = Field(
        ...,
        description="Sources of uncertainty or missing parameters.",
    )
    validation_status: str = Field(
        ...,
        description="Status of verification/validation (e.g. VALIDATED, PENDING, REJECTED).",
    )

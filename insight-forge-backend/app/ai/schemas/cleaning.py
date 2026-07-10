"""
Insight Forge V2 — Data Cleaning Schemas.

Defines Pydantic models for data quality issues, cleaning recommendations, and certification summaries.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class CleaningRecommendation(BaseModel):
    """Structured remediation recommendation for a detected data quality issue."""

    issue_type: str = Field(
        ...,
        description="Category of the quality issue (e.g. MISSING_VALUES, DUPLICATE_ROWS, CASING_INCONSISTENCY).",
    )
    affected_columns: list[str] = Field(
        default_factory=list,
        description="Target columns impacted by the issue.",
    )
    severity: str = Field(
        ...,
        description="Severity assessment of the issue (Low, Medium, High, Critical).",
    )
    recommended_action: str = Field(
        ...,
        description="Remediation suggestion (e.g. Normalize Casing, Flag for manual review, Remove duplicates).",
    )
    reasoning: str = Field(
        ...,
        description="Explanation behind selecting this specific cleaning action.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated certainty score in this recommendation.",
    )
    evidence: str = Field(
        ...,
        description="Factual metadata trace justifying the recommendation.",
    )


class TrustedDatasetSummary(BaseModel):
    """Consolidated report documenting quality health score and certification level."""

    overall_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Aggregate quality score representing general dataset trust.",
    )
    total_issues_detected: int = Field(
        ...,
        ge=0,
        description="Total distinct issues detected across columns and rows.",
    )
    critical_issues_count: int = Field(
        ...,
        ge=0,
        description="Count of critical severity issues that block standard analytics.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Compilation of general dataset or validation warning statements.",
    )
    cleaning_recommendations: list[CleaningRecommendation] = Field(
        default_factory=list,
        description="List of recommendations proposed by the engine.",
    )
    certification_status: str = Field(
        ...,
        description="Final certification status (Certified, Certified with Warnings, Requires Review, Not Certified).",
    )


class CleaningLogEntry(BaseModel):
    """Audit log tracking proposal and state metrics for cleaning actions."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamps audit check execution.",
    )
    issue: str = Field(..., description="Short summary of the data quality issue.")
    recommendation: str = Field(..., description="Action proposed to address the issue.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Recommendation confidence level.",
    )
    evidence: str = Field(..., description="Statistical or structural validation backing.")
    status: str = Field(
        "PROPOSED",
        description="Action state (e.g. PROPOSED, APPROVED, REJECTED, APPLIED).",
    )

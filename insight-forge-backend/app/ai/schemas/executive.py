"""
Insight Forge V2 — Executive Report schemas.

Defines Pydantic models for ExecutiveFinding, ExecutiveRecommendation, and ExecutiveReport.
"""

from pydantic import BaseModel, Field


class ExecutiveFinding(BaseModel):
    """Pydantic model representing a high-level business finding for C-suite view."""

    title: str = Field(..., description="Short title of the finding.")
    description: str = Field(..., description="High-level description summarizing what occurred.")
    evidence: str = Field(..., description="Analytical backing or statistical values supporting this finding.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mathematical backing certainty.")
    business_impact: str = Field(..., description="Impact description (cost, quality, forecasting skew).")


class ExecutiveRecommendation(BaseModel):
    """Pydantic model representing a prioritized recommendation."""

    title: str = Field(..., description="Recommendation title.")
    priority: str = Field(..., description="Priority tier (High, Medium, Low).")
    estimated_roi: float = Field(..., description="Percentage ROI projection.")
    timeline: str = Field(..., description="Estimated timeline.")
    owner: str = Field(..., description="Actionable role owner.")


class ExecutiveReport(BaseModel):
    """Consolidated executive dashboard summary report model."""

    executive_summary: str = Field(..., description="Concise high-level summary paragraph for executives.")
    business_health_score: float = Field(..., ge=0.0, le=100.0, description="Calculated metric health indicator score (0-100).")
    key_findings: list[ExecutiveFinding] = Field(default_factory=list)
    strategic_recommendations: list[ExecutiveRecommendation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

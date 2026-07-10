"""
Insight Forge V2 — Strategic Recommendation and Opportunity Schemas.

Defines Pydantic models for BusinessOpportunity, RiskAssessment, StrategicRecommendation, and StrategySummary.
"""

from pydantic import BaseModel, Field


class BusinessOpportunity(BaseModel):
    """Pydantic model representing an identified business opportunity (growth/cost-cut)."""

    title: str = Field(..., description="Short summary of the strategic opportunity.")
    description: str = Field(..., description="Detailed description of the opportunity mechanics.")
    priority: str = Field(..., description="Opportunity priority level (High, Medium, Low).")
    estimated_roi: float = Field(..., description="Estimated percentage return on investment (e.g. 150.0 for 150%).")
    business_impact: str = Field(..., description="Expected impact summary.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in opportunity realization.")
    evidence: str = Field(..., description="Direct validated hypothesis or statistic backing this opportunity.")


class RiskAssessment(BaseModel):
    """Pydantic model representing an operational or data quality risk factor."""

    title: str = Field(..., description="Risk title.")
    description: str = Field(..., description="Detailed explanation of the risk scenario.")
    priority: str = Field(..., description="Risk impact severity priority (High, Medium, Low).")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Likelihood or analytical confidence in the risk occurrence.")
    evidence: str = Field(..., description="Supporting data quality anomalies or warnings indicating this risk.")


class StrategicRecommendation(BaseModel):
    """Pydantic model representing an actionable recommendation based on validated evidence."""

    title: str = Field(..., description="Actionable recommendation title.")
    description: str = Field(..., description="Description of the proposed solution.")
    priority: str = Field(..., description="Priority level (High, Medium, Low).")
    estimated_roi: float = Field(..., description="Estimated percentage ROI.")
    business_impact: str = Field(..., description="Expected positive business outcomes.")
    implementation_effort: str = Field(..., description="Complexity/Effort estimation (High, Medium, Low).")
    timeline: str = Field(..., description="Expected execution timeline (e.g. '1-2 weeks', '1 month').")
    owner: str = Field(..., description="Suggested role or owner responsible for implementation.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mathematical backing confidence.")
    evidence: str = Field(..., description="Validated business hypothesis or audit trails justifying this action.")


class StrategySummary(BaseModel):
    """Consolidated summary of opportunities, risk assessments, and recommendations."""

    opportunities: list[BusinessOpportunity] = Field(default_factory=list)
    recommendations: list[StrategicRecommendation] = Field(default_factory=list)
    risks: list[RiskAssessment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

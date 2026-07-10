"""
Insight Forge V2 — Anomaly Detection and Business Insight Schemas.

Defines Pydantic models for anomalies, statistical skeletal splits, and strategic business insights.
"""

from pydantic import BaseModel, Field


class AnomalyDetection(BaseModel):
    """Pydantic model representing a detected data anomaly or outlier pattern."""

    title: str = Field(..., description="Short summary of the data quality anomaly.")
    description: str = Field(..., description="Detailed description of the flagged data behavior.")
    affected_columns: list[str] = Field(default_factory=list, description="Target columns containing the anomaly.")
    evidence: str = Field(..., description="Factual numerical trace or bound violations backing this flag.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Estimated certainty score.")
    severity: str = Field(..., description="Severity category (Low, Medium, High, Critical).")
    recommendation: str = Field(..., description="Actionable cleaning or review recommendation.")


class BusinessInsight(BaseModel):
    """Pydantic model representing a strategic business recommendation derived from validated findings."""

    title: str = Field(..., description="Short title of the business insight.")
    description: str = Field(..., description="Contextual explanation of what the patterns imply.")
    affected_columns: list[str] = Field(default_factory=list, description="Target columns supporting this insight.")
    evidence: str = Field(..., description="Validated statistical test results justifying this framing.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mathematical confidence score.")
    business_impact: str = Field(..., description="Estimated business value or impact summary.")
    severity: str = Field(..., description="Severity or priority (Low, Medium, High, Critical).")
    recommendation: str = Field(..., description="Actionable strategic decision proposal.")


class InsightSummary(BaseModel):
    """Consolidated summary model containing all parsed anomalies and insights."""

    anomalies: list[AnomalyDetection] = Field(default_factory=list)
    insights: list[BusinessInsight] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

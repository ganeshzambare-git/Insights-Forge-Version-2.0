"""
Insight Forge V2 — AI Data Analyst Schemas.

Defines Pydantic models for business KPIs, metadata, and generated business questions.
"""

from pydantic import BaseModel, Field


class KPIMetadata(BaseModel):
    """Business KPI details inferred from the dataset structure."""

    kpi_name: str = Field(..., description="Inferred business KPI name (e.g. Revenue, Average Order Value).")
    description: str = Field(..., description="Explanation of what this KPI measures.")
    required_columns: list[str] = Field(
        default_factory=list,
        description="Target columns needed to calculate this KPI.",
    )
    aggregation_type: str = Field(
        ...,
        description="Aggregation method recommended (e.g. SUM, AVG, COUNT, ratio, percentage).",
    )
    business_purpose: str = Field(
        ...,
        description="Strategic business intent or decision support enabled by this KPI.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score in the KPI mapping.",
    )


class BusinessQuestion(BaseModel):
    """Framed business question addressable using the dataset columns."""

    question_text: str = Field(..., description="Framed business query (e.g. Which region generates the most sales?).")
    priority: str = Field(
        ...,
        description="Priority level for business analysis (High, Medium, Low).",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in answerability of this question.",
    )
    required_columns: list[str] = Field(
        default_factory=list,
        description="Target columns needed to answer this question.",
    )
    reasoning: str = Field(
        ...,
        description="Business logic or justification for prioritizing this query.",
    )


class AnalystLLMResponse(BaseModel):
    """Consolidated LLM output schema for business framing analysis."""

    discovered_kpis: list[KPIMetadata] = Field(
        default_factory=list,
        description="List of business KPIs identified.",
    )
    business_questions: list[BusinessQuestion] = Field(
        default_factory=list,
        description="List of strategic business questions.",
    )
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in domain identification and framing.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings regarding data gaps or limitations.",
    )

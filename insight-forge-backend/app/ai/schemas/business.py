"""
Insight Forge V2 — Business Analyst schemas.

Defines Pydantic models for Root Cause Analysis, Business Hypotheses, and Business Summaries.
"""

from pydantic import BaseModel, Field


class RootCause(BaseModel):
    """Pydantic model representing a structured Root Cause analysis (e.g. 5 Whys traceback)."""

    title: str = Field(..., description="Short title of the identified root cause.")
    description: str = Field(..., description="Step-by-step breakdown of the causal factors.")
    evidence: str = Field(..., description="Direct factual indicators justifying this root cause chain.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mathematical certainty score.")
    business_impact: str = Field(..., description="Estimated cost or benefit description.")
    supporting_findings: list[str] = Field(default_factory=list, description="Findings or anomalies backing this chain.")


class BusinessHypothesis(BaseModel):
    """Pydantic model representing a proposed business driver that requires validation against findings."""

    title: str = Field(..., description="Short title of the hypothesis.")
    description: str = Field(..., description="Detailed business statement/explanation.")
    evidence: str = Field(..., description="Evidence support statement or rejection rationale.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Estimated supporting weight.")
    business_impact: str = Field(..., description="Business significance statement.")
    supporting_findings: list[str] = Field(default_factory=list, description="Analyst findings used to test the hypothesis.")
    status: str = Field("Pending", description="Hypothesis status (Validated, Rejected, Pending).")


class BusinessAnalysisSummary(BaseModel):
    """Consolidated summary model containing all root causes and hypotheses."""

    root_causes: list[RootCause] = Field(default_factory=list)
    generated_hypotheses: list[BusinessHypothesis] = Field(default_factory=list)
    validated_hypotheses: list[BusinessHypothesis] = Field(default_factory=list)
    rejected_hypotheses: list[BusinessHypothesis] = Field(default_factory=list)
    business_reasoning: list[str] = Field(default_factory=list)

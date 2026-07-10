"""
Insight Forge V2 — Orchestration Pipeline Metrics.

Defines Pydantic models for step-level execution time metrics and pipeline results.
"""

from typing import Any
from pydantic import BaseModel, Field


class AgentStepMetric(BaseModel):
    """Pydantic model representing timing and outcome data for a single agent step."""

    agent_name: str = Field(..., description="Name of the executed agent.")
    execution_time_ms: float = Field(..., description="Execution time of the step in milliseconds.")
    status: str = Field(..., description="Outcome status of the step (Success, Failure).")
    error: str | None = Field(None, description="Detailed error description if status is Failure.")


class OrchestratedPipelineResult(BaseModel):
    """Pydantic model representing the overall output of the orchestrated multi-agent pipeline."""

    success: bool = Field(..., description="Overall pipeline execution success indicator.")
    metrics: list[AgentStepMetric] = Field(default_factory=list, description="List of step metrics.")
    consolidated_report: dict[str, Any] = Field(default_factory=dict, description="Consolidated report dictionary.")
    warnings: list[str] = Field(default_factory=list, description="Warnings aggregated across execution steps.")

"""
Insight Forge V2 — Unit Tests for Multi-Agent Workflow Orchestrator.

Validates end-to-end sequential pipeline execution, context data propagation,
failsafe abort triggers on step failure, and telemetry timing tracking.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AIWorkflowOrchestrator,
    AgentContractResponse,
    ConfidenceModel,
)
from app.ai.llm.provider import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Generic LLM Mock for workflow orchestration tests."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "mock"

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "mock"


class MockAgentWithResponse:
    """Helper to mock execute responses from BaseAIAgent classes."""

    def __init__(self, name: str, success: bool, findings: dict[str, Any], errors: list[str] | None = None) -> None:
        self.name = name
        self.success = success
        self.findings = findings
        self.errors = errors or []

    async def execute(self, context: AIContext, *args: Any, **kwargs: Any) -> AgentContractResponse:
        return AgentContractResponse(
            success=self.success,
            agent_name=self.name,
            findings=self.findings,
            confidence=ConfidenceModel(
                confidence_score=0.9,
                confidence_level="HIGH",
                explanation="explanation",
                uncertainty="none",
                validation_status="VALIDATED",
            ),
            evidence=[],
            errors=self.errors,
        )


@pytest.mark.asyncio
async def test_successful_orchestrated_pipeline_flow() -> None:
    """Verify that a successful end-to-end pipeline run calls all four agents and aggregates results."""
    # 1. Setup mock agents with successful responses
    engineer = MockAgentWithResponse(
        name="data-engineer",
        success=True,
        findings={"dataset_name": "quarterly_finances", "columns": ["Rev", "Cost"]},
    )
    analyst = MockAgentWithResponse(
        name="data-analyst",
        success=True,
        findings={
            "discovered_kpis": [],
            "business_questions": [],
            "kpi_metadata": {},
            "confidence": 0.95,
            "warnings": ["Low rows"],
            "statistical_results": [],
            "trend_analysis": [],
            "correlation_results": [],
            "analyst_evidence": [],
            "detected_anomalies": [],
            "business_insights": [],
            "validated_findings": [],
            "analyst_recommendations": [],
        },
    )
    business = MockAgentWithResponse(
        name="business-analyst",
        success=True,
        findings={
            "root_causes": [],
            "generated_hypotheses": [],
            "validated_hypotheses": [],
            "rejected_hypotheses": [],
            "business_reasoning": [],
            "business_opportunities": [],
            "strategic_recommendations": [],
            "risks": [],
            "implementation_priorities": [],
        },
    )
    executive = MockAgentWithResponse(
        name="executive-report",
        success=True,
        findings={
            "executive_summary": "Overall healthy.",
            "business_health_score": 100.0,
            "key_findings": [],
            "strategic_recommendations": [],
            "warnings": [],
        },
    )

    context = AIContext(
        tenant_id="tenant-orch-1",
        dataset_metadata={
            "dataset_name": "quarterly_finances",
            "columns": ["Rev", "Cost"],
        },
    )

    orchestrator = AIWorkflowOrchestrator()
    # Execute (using mock agents casted as actual agent wrappers for python type compatibility)
    result = await orchestrator.run_pipeline(
        context,
        engineer,  # type: ignore
        analyst,  # type: ignore
        business,  # type: ignore
        executive,  # type: ignore
    )

    assert result.success is True
    assert len(result.metrics) == 4

    # Verify order of metrics matches dependency sequence
    assert result.metrics[0].agent_name == "data-engineer"
    assert result.metrics[0].status == "Success"
    assert result.metrics[1].agent_name == "data-analyst"
    assert result.metrics[2].agent_name == "business-analyst"
    assert result.metrics[3].agent_name == "executive-report"

    # Verify timing values are populated
    for m in result.metrics:
        assert m.execution_time_ms >= 0.0

    # Verify consolidated output report contains integrated findings from executive generator
    assert result.consolidated_report["executive_summary"] == "Overall healthy."
    assert result.consolidated_report["business_health_score"] == 100.0


@pytest.mark.asyncio
async def test_orchestration_failsafe_abort() -> None:
    """Verify that a failure in one of the agents halts execution immediately without executing subsequent steps."""
    engineer = MockAgentWithResponse(
        name="data-engineer",
        success=True,
        findings={"dataset_name": "test_set", "columns": ["col"]},
    )
    # Analyst fails validation or math processing
    analyst = MockAgentWithResponse(
        name="data-analyst",
        success=False,
        findings={},
        errors=["Invalid data profiles provided"],
    )
    business = MockAgentWithResponse(
        name="business-analyst",
        success=True,
        findings={},
    )
    executive = MockAgentWithResponse(
        name="executive-report",
        success=True,
        findings={},
    )

    context = AIContext(
        tenant_id="tenant-orch-2",
        dataset_metadata={"dataset_name": "test_set", "columns": ["col"]},
    )

    orchestrator = AIWorkflowOrchestrator()
    result = await orchestrator.run_pipeline(
        context,
        engineer,  # type: ignore
        analyst,  # type: ignore
        business,  # type: ignore
        executive,  # type: ignore
    )

    assert result.success is False
    # Metrics should stop at the failing step (len should be 2: engineer and failing analyst)
    assert len(result.metrics) == 2
    assert result.metrics[1].agent_name == "data-analyst"
    assert result.metrics[1].status == "Failure"
    assert "Invalid data profiles provided" in result.metrics[1].error

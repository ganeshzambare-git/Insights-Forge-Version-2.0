"""
Insight Forge V2 — Unit Tests for Executive Report Generator.

Validates executive summary text compiler, business health score algorithms,
 C-suite priority rankings, empty fallback cases, and agent integration.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIExecutiveReportGenerator,
    ExecutiveReport,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.utils.executive import (
    calculate_overall_business_health,
    generate_executive_summary,
    build_executive_report,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for AIExecutiveReportGenerator tests."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "Executive report mock response"

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "Executive report mock chat"


def test_business_health_score_calculations() -> None:
    """Verify health score penalty deductions and opportunity bonuses."""
    anomalies = [
        {"title": "Outlier in Price", "severity": "High"},
        {"title": "Spike in Cost", "severity": "Medium"},
    ]
    opportunities = [
        {"title": "Scale inbound channels", "estimated_roi": 250.0},
    ]

    # Starting at 100.0:
    # Price outlier: -10
    # Cost spike: -5
    # Scale opportunity (ROI 250% >= 200%): +5
    # Result should be: 100 - 10 - 5 + 5 = 90.0
    score = calculate_overall_business_health(anomalies, opportunities)
    assert score == 90.0

    # Ceiling/Floor check
    empty_anomalies = []
    highly_positive_opps = [{"title": "Growth", "estimated_roi": 300.0}] * 10
    score_ceil = calculate_overall_business_health(empty_anomalies, highly_positive_opps)
    assert score_ceil == 100.0  # capped at 100.0

    severe_anomalies = [{"title": "Crash", "severity": "Critical"}] * 20
    score_floor = calculate_overall_business_health(severe_anomalies, [])
    assert score_floor == 0.0  # floored at 0.0


def test_summary_text_generation() -> None:
    """Verify C-suite summary text contains status indicators based on health score."""
    sum_optimal = generate_executive_summary("sales_log", 1, 2, 92.5)
    assert "sales_log" in sum_optimal
    assert "92.5%" in sum_optimal
    assert "stable and optimal" in sum_optimal

    sum_critical = generate_executive_summary("retail_log", 10, 1, 45.0)
    assert "critical, requiring immediate engineering" in sum_critical


def test_empty_input_handling() -> None:
    """Verify engine handles empty context lists without crashes."""
    report = build_executive_report("empty_log", [], [], [], [], [])
    assert isinstance(report, ExecutiveReport)
    assert report.business_health_score == 100.0
    assert len(report.key_findings) == 0
    assert len(report.strategic_recommendations) == 0


@pytest.mark.asyncio
async def test_executive_report_agent_integration_and_memory() -> None:
    """Verify AIExecutiveReportGenerator execute compiles dashboard findings and updates memory."""
    llm = MockLLMProvider()
    agent = AIExecutiveReportGenerator(name="test-executive-generator", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-executive-1",
        dataset_metadata={
            "dataset_name": "annual_earnings_profile",
            "columns": ["Revenue", "Margin"],
            "detected_anomalies": [
                {
                    "title": "Outliers Detected in Revenue",
                    "description": "Revenue outliers.",
                    "affected_columns": ["Revenue"],
                    "evidence": "val: 9999",
                    "confidence": 0.95,
                    "severity": "High",
                    "recommendation": "Verify raw source logs.",
                }
            ],
            "business_insights": [
                {
                    "title": "Significant Regression Trend: Revenue vs Margin",
                    "affected_columns": ["Revenue", "Margin"],
                    "confidence": 0.98,
                    "evidence": "Slope: 1.5, R2: 0.8",
                    "business_impact": "Predictable margin forecast.",
                }
            ],
            "business_opportunities": [
                {
                    "title": "ETL Pipeline De-duplication",
                    "estimated_roi": 700.0,
                }
            ],
            "strategic_recommendations": [
                {
                    "title": "Audit Ingestion Payload De-duplication",
                    "priority": "High",
                    "estimated_roi": 700.0,
                    "timeline": "1 week",
                    "owner": "Data Lead",
                }
            ],
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "executive_summary" in findings
    assert "business_health_score" in findings
    assert "key_findings" in findings
    assert "strategic_recommendations" in findings
    assert "warnings" in findings

    # Health score: 100 - 10 (High anomaly) + 5 (ROI >= 200 opportunity) = 95.0
    assert findings["business_health_score"] == 95.0

    # Key findings should compile both anomalies and insights
    kf = findings["key_findings"]
    assert len(kf) == 2
    titles = [f["title"] for f in kf]
    assert any("Anomaly: Outliers Detected in Revenue" in t for t in titles)
    assert any("Insight: Significant Regression Trend" in t for t in titles)

    # Strategic recommendations check
    sr = findings["strategic_recommendations"]
    assert len(sr) == 1
    assert sr[0]["title"] == "Audit Ingestion Payload De-duplication"
    assert sr[0]["priority"] == "High"

    # Verify agent memory tracks compiled logs
    assert "Initiated executive summary compilation and dashboard ranking." in agent.memory.reasoning_history
    assert any("Report health score calculated at 95.0%" in f for f in agent.memory.accepted_findings)
    assert any("report_health:95.0" in ref for ref in agent.memory.evidence_references)

"""
Insight Forge V2 — Unit Tests for Strategy Engine.

Validates ROI calculation math, priority scoring, evidence filtering (rejection cases),
risk assessments, and business analyst agent integration.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIBusinessAnalyst,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.utils.strategy import (
    calculate_roi,
    score_priority_by_roi,
    evaluate_strategy_recommendations,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for AIBusinessAnalyst tests."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "Business Analyst mock response"

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "Business Analyst mock chat"


def test_roi_calculation() -> None:
    """Verify ROI percentage math calculation."""
    roi = calculate_roi(150000.0, 50000.0)
    assert roi == 200.0  # (150k - 50k)/50k = 2 * 100% = 200%

    # Zero cost boundary check
    roi_zero = calculate_roi(100.0, 0.0)
    assert roi_zero == 0.0


def test_priority_scoring() -> None:
    """Verify priority mapping based on ROI and effort scale."""
    p1 = score_priority_by_roi(600.0, "Low")
    assert p1 == "High"

    p2 = score_priority_by_roi(200.0, "Medium")
    assert p2 == "Medium"

    p3 = score_priority_by_roi(100.0, "High")
    assert p3 == "Low"


def test_evidence_filtering_and_rejection() -> None:
    """Verify recommendations are rejected/skipped if their supporting hypotheses are rejected."""
    validated_hyp = [
        {
            "title": "Ingestion Double-Logging in Revenue",
            "description": "Double logging.",
            "evidence": "Outliers found.",
            "confidence": 0.90,
            "supporting_findings": ["Significant Regression Trend"],
            "status": "Validated",
        }
    ]

    rejected_hyp = [
        {
            "title": "Organic Market Growth in Revenue",
            "description": "True growth.",
            "evidence": "Rejected due to outliers.",
            "confidence": 0.15,
            "supporting_findings": ["Significant Regression Trend"],
            "status": "Rejected",
        }
    ]

    root_causes = [
        {
            "title": "Root Cause of Outliers Detected in Revenue",
            "description": "5 Whys steps",
            "evidence": "outlier values",
            "confidence": 0.85,
        }
    ]

    summary = evaluate_strategy_recommendations(validated_hyp, rejected_hyp, root_causes)

    # Ingestion recommendations must be generated
    recs = summary.recommendations
    assert len(recs) == 1
    assert "Audit Ingestion Payload" in recs[0].title
    assert recs[0].estimated_roi == 700.0

    # Growth campaigns must be skipped (no "Deploy Additional Inbound Spend" recommendations)
    assert not any("Inbound Spend" in r.title for r in recs)

    # Skipper warning should be populated
    assert len(summary.warnings) == 1
    assert "Organic Market Growth" in summary.warnings[0]

    # Risks must contain outlier decision model risk
    assert len(summary.risks) == 1
    assert "Decision Model Metric Corruption" in summary.risks[0].title


@pytest.mark.asyncio
async def test_business_analyst_strategy_integration_and_memory() -> None:
    """Verify agent execution compiles strategic opportunities, priorities, and updates memory."""
    llm = MockLLMProvider()
    agent = AIBusinessAnalyst(name="test-business-analyst-strategy", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-strategy-1",
        dataset_metadata={
            "dataset_name": "quarterly_profitability_audit",
            "columns": ["X", "Y"],
            "detected_anomalies": [
                {
                    "title": "Outliers Detected in Y",
                    "description": "Outliers found.",
                    "affected_columns": ["Y"],
                    "evidence": "Value: 900",
                    "confidence": 0.95,
                    "severity": "High",
                }
            ],
            "business_insights": [
                {
                    "title": "Significant Regression Trend: X vs Y",
                    "affected_columns": ["X", "Y"],
                    "confidence": 0.98,
                    "evidence": "Slope: 1.5, R2: 0.8",
                }
            ],
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "business_opportunities" in findings
    assert "strategic_recommendations" in findings
    assert "risks" in findings
    assert "implementation_priorities" in findings

    # Ingestion opportunity must be created (since Y contains outlier anomaly, Technical duplicate hyp is validated)
    opps = findings["business_opportunities"]
    assert len(opps) == 1
    assert "ETL Pipeline De-duplication" in opps[0]["title"]

    recs = findings["strategic_recommendations"]
    assert len(recs) == 1
    assert "Audit Ingestion Payload De-duplication" in recs[0]["title"]
    assert recs[0]["estimated_roi"] == 700.0

    # Implementation priorities list should contain recommendation titles in order of ROI
    assert findings["implementation_priorities"] == ["Audit Ingestion Payload De-duplication"]

    # Verify risk assessment is populated
    assert len(findings["risks"]) == 1
    assert "Decision Model Metric Corruption Risk" in findings["risks"][0]["title"]

    # Verify agent memory tracks strategy steps
    assert "Initiated strategy recommendation synthesis and ROI validation." in agent.memory.reasoning_history
    assert any("Identified Opportunity: ETL Pipeline De-duplication (ROI: 700.0%)" in f for f in agent.memory.accepted_findings)
    assert any("opportunity_ref:ETL Pipeline De-duplication" in ref for ref in agent.memory.evidence_references)

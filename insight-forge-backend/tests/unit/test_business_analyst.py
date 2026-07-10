"""
Insight Forge V2 — Unit Tests for AI Business Analyst.

Validates 5 Whys root cause calculations, competing hypothesis mapping, evidence-based
ranking/rejection logic, memory updates, and agent execution workflows.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIBusinessAnalyst,
    RootCause,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.utils.business import (
    perform_5_whys,
    generate_competing_hypotheses,
    evaluate_and_rank_hypotheses,
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


def test_5_whys_generation() -> None:
    """Verify that 5 Whys builds a complete trace step chain for anomalies."""
    anomaly_outlier = {
        "title": "Outliers Detected in Price",
        "description": "Found entries violating normal distribution bounds.",
        "affected_columns": ["Price"],
        "evidence": "Value: 5000.00",
        "confidence": 0.95,
        "severity": "High",
    }

    rc = perform_5_whys(anomaly_outlier)
    assert isinstance(rc, RootCause)
    assert rc.supporting_findings == ["Outliers Detected in Price"]

    # Verify description has 5 Whys steps
    why_lines = rc.description.split("\n")
    assert len(why_lines) == 5
    assert "1. Why: Extreme metric value" in why_lines[0]
    assert "Price" in why_lines[0]
    assert "5. Why: Lack of strict application threshold" in why_lines[4]

    # Verify spike anomaly path
    anomaly_spike = {
        "title": "Sudden Spike in Revenue",
        "affected_columns": ["Revenue"],
        "evidence": "Z: 4.5",
    }
    rc_spike = perform_5_whys(anomaly_spike)
    assert "Sudden sequential step-change spike" in rc_spike.description


def test_competing_hypotheses_generation() -> None:
    """Verify competing hypotheses are framed (Organic Growth vs Ingestion Error)."""
    insight = {
        "title": "Significant Regression Trend: Sales vs Profit",
        "affected_columns": ["Sales", "Profit"],
        "confidence": 0.95,
    }
    anomalies = []

    hypotheses = generate_competing_hypotheses(insight, anomalies)
    assert len(hypotheses) == 2

    titles = [h.title for h in hypotheses]
    assert any("Organic Market Growth" in t for t in titles)
    assert any("Ingestion Double-Logging" in t for t in titles)


def test_hypothesis_ranking_and_rejection_rules() -> None:
    """Verify technical/organic validation rules and rejection triggers under anomalies."""
    insight = {
        "title": "Significant Regression Trend: Clicks vs Conversions",
        "affected_columns": ["Clicks", "Conversions"],
        "confidence": 0.98,
    }

    # Case 1: Ingestion anomalies are present in 'Clicks' column
    anomalies_present = [
        {"title": "Outliers in Clicks", "affected_columns": ["Clicks"], "evidence": "val: 9999"}
    ]
    hyps_with_anomaly = generate_competing_hypotheses(insight, anomalies_present)
    eval_with_anomaly = evaluate_and_rank_hypotheses(hyps_with_anomaly, anomalies_present)

    # Technical duplicate hypothesis must be validated, Organic growth rejected
    validated = eval_with_anomaly["validated"]
    rejected = eval_with_anomaly["rejected"]

    assert len(validated) == 1
    assert "Ingestion Double-Logging" in validated[0].title
    assert validated[0].status == "Validated"

    assert len(rejected) == 1
    assert "Organic Market Growth" in rejected[0].title
    assert rejected[0].status == "Rejected"

    # Case 2: No anomalies present
    hyps_clean = generate_competing_hypotheses(insight, [])
    eval_clean = evaluate_and_rank_hypotheses(hyps_clean, [])

    validated_clean = eval_clean["validated"]
    rejected_clean = eval_clean["rejected"]

    assert len(validated_clean) == 1
    assert "Organic Market Growth" in validated_clean[0].title
    assert validated_clean[0].status == "Validated"

    assert len(rejected_clean) == 1
    assert "Ingestion Double-Logging" in rejected_clean[0].title
    assert rejected_clean[0].status == "Rejected"


@pytest.mark.asyncio
async def test_business_analyst_agent_integration_and_memory() -> None:
    """Verify AIBusinessAnalyst execute integrates engine processes and updates memory."""
    llm = MockLLMProvider()
    agent = AIBusinessAnalyst(name="test-business-analyst", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-business-1",
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
    assert "root_causes" in findings
    assert "generated_hypotheses" in findings
    assert "validated_hypotheses" in findings
    assert "rejected_hypotheses" in findings
    assert "business_reasoning" in findings

    # Root Cause (5 Whys) should be parsed
    assert len(findings["root_causes"]) == 1
    assert "Outliers Detected in Y" in findings["root_causes"][0]["title"]

    # Since anomaly was present in Y, Technical hypothesis should be validated and Organic rejected
    val_hyps = findings["validated_hypotheses"]
    rej_hyps = findings["rejected_hypotheses"]

    assert len(val_hyps) == 1
    assert "Ingestion Double-Logging" in val_hyps[0]["title"]

    assert len(rej_hyps) == 1
    assert "Organic Market Growth" in rej_hyps[0]["title"]

    # Verify memory tracks 5 Whys and validation steps
    assert "Initiated operational root cause analysis (5 Whys)." in agent.memory.reasoning_history
    assert any("Root cause identified:" in f for f in agent.memory.accepted_findings)
    assert any("validated_hyp:" in ref for ref in agent.memory.evidence_references)
    assert any("rejected_hyp:" in ref for ref in agent.memory.evidence_references)

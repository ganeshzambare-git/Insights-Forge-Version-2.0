"""
Insight Forge V2 — Unit Tests for Anomaly Detection and Business Insight Engine.

Validates outlier detection, spike/drop triggers, skepticism-based validation,
insight generation rules, and data analyst integration checks.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIDataAnalyst,
    StatisticalSummary,
    CorrelationResult,
    TrendAnalysis,
    StatisticalTest,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.utils.insights import (
    detect_outliers,
    detect_spikes_drops,
    validate_statistical_findings,
    generate_insights_and_anomalies,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider returning static response models."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        from app.ai import AnalystLLMResponse, KPIMetadata, BusinessQuestion
        if schema is AnalystLLMResponse:
            return AnalystLLMResponse(
                discovered_kpis=[
                    KPIMetadata(
                        kpi_name="Revenue",
                        description="Revenue sums",
                        required_columns=["Val"],
                        aggregation_type="SUM",
                        business_purpose="Purpose",
                        confidence=0.9,
                    )
                ],
                business_questions=[
                    BusinessQuestion(
                        question_text="How to improve Val?",
                        priority="High",
                        confidence=0.9,
                        required_columns=["Val"],
                        reasoning="Reasoning",
                    )
                ],
                overall_confidence=0.9,
                warnings=[],
            )
        return "Raw text response"

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "Raw chat response"


def test_outlier_detection() -> None:
    """Verify standard deviation-based outlier flagging."""
    series = [10.0, 11.0, 10.5, 9.5, 10.2, 1000.0]  # 1000.0 is a clear outlier
    anomalies = detect_outliers(series, "Revenue")
    assert len(anomalies) == 1
    assert anomalies[0].affected_columns == ["Revenue"]
    assert "1000.00" in anomalies[0].evidence
    assert anomalies[0].severity == "High"


def test_spike_drop_detection() -> None:
    """Verify sudden sequential spikes and drops flagging."""
    series = [10.0, 11.0, 12.0, 11.5, 12.5, 100.0, 101.0, 102.0]  # jump from 12.5 to 100 is a spike
    anomalies = detect_spikes_drops(series, "Volume")
    assert len(anomalies) == 1
    assert "spike" in anomalies[0].title.lower()
    assert anomalies[0].affected_columns == ["Volume"]


def test_skepticism_test_validation() -> None:
    """Verify skepticism filter challenges weak, low-sample, or non-significant tests."""
    stats = StatisticalSummary(
        correlations=[
            CorrelationResult(
                target_columns=["A", "B"],
                confidence=0.99,  # Significant
                significance=0.01,
                evidence="Sample count: 10",
                interpretation="Strong",
                correlation_coefficient=0.85,  # Strong r
            ),
            CorrelationResult(
                target_columns=["X", "Y"],
                confidence=0.80,  # NOT significant
                significance=0.20,
                evidence="Sample count: 10",
                interpretation="Weak",
                correlation_coefficient=0.15,  # Weak r
            ),
            CorrelationResult(
                target_columns=["P", "Q"],
                confidence=0.99,
                significance=0.01,
                evidence="Sample count: 3",  # Sample size too small (< 5)
                interpretation="Strong",
                correlation_coefficient=0.95,
            ),
        ],
        trends=[
            TrendAnalysis(
                analysis_type="Simple Linear Regression",
                target_columns=["Time", "Sales"],
                confidence=0.92,  # NOT significant (< 95%)
                significance=0.08,
                evidence="y = 2*x + 10",
                interpretation="Trend",
                slope=2.0,
                intercept=10.0,
                r_squared=0.25,
            )
        ],
    )

    res = validate_statistical_findings(stats, n_rows=10)
    validated = res["validated"]
    rejected = res["rejected"]

    # Only A vs B correlation should be validated
    assert len(validated["correlations"]) == 1
    assert validated["correlations"][0].target_columns == ["A", "B"]

    # X vs Y (weak/insignificant) and P vs Q (N=3) must be rejected
    assert len(rejected) == 3  # 2 correlations + 1 trend
    assert any("X" in r and "Y" in r for r in rejected)
    assert any("P" in r and "Q" in r for r in rejected)
    assert any("Time" in r and "Sales" in r for r in rejected)


def test_business_insight_generation() -> None:
    """Verify business-readable insight mapping from validated tests."""
    stats = StatisticalSummary(
        trends=[
            TrendAnalysis(
                analysis_type="Simple Linear Regression",
                target_columns=["X", "Y"],
                confidence=0.98,
                significance=0.02,
                evidence="y = 1.5*x + 5.0",
                interpretation="High Growth",
                slope=1.5,
                intercept=5.0,
                r_squared=0.75,
            ),
            TrendAnalysis(
                analysis_type="Sequence Trend Analysis",
                target_columns=["Timeline"],
                confidence=0.90,
                significance=0.05,
                evidence="Growth rate: 35.00%",
                interpretation="High Growth Sequence",
                slope=0.35,
                intercept=10.0,
                r_squared=0.5,
            ),
        ],
        tests=[
            StatisticalTest(
                analysis_type="Chi-Square Test of Independence",
                target_columns=["Category", "Region"],
                confidence=0.97,
                significance=0.03,
                evidence="Chi2: 15.5",
                interpretation="Dependency",
            )
        ],
    )

    df_dict = [{"X": 1.0, "Y": 2.0}, {"X": 2.0, "Y": 4.0}, {"X": 3.0, "Y": 6.0}, {"X": 4.0, "Y": 8.0}, {"X": 5.0, "Y": 10.0}]
    col_types = {"X": "float", "Y": "float"}

    summary = generate_insights_and_anomalies(df_dict, col_types, stats)

    # Validate that Simple Linear Regression, Sequence Growth, and Chi-Square yield insights
    insights = {i.title: i for i in summary.insights}
    assert any("Significant Regression Trend" in t for t in insights)
    assert any("High Growth Performance" in t for t in insights)
    assert any("Categorical Dependency" in t for t in insights)


@pytest.mark.asyncio
async def test_analyst_insights_integration_and_memory() -> None:
    """Verify AIDataAnalyst execute maps anomalies, insights, validated lists, and updates memory."""
    llm = MockLLMProvider()
    agent = AIDataAnalyst(name="test-analyst", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-insights-1",
        dataset_metadata={
            "dataset_name": "cohort_finance_records",
            "columns": ["X", "Y"],
            "sample_rows": [
                {"X": 1, "Y": 10},
                {"X": 2, "Y": 12},
                {"X": 3, "Y": 11},
                {"X": 4, "Y": 13},
                {"X": 5, "Y": 1000},  # outlier value
            ],
            "dataset_profile": {
                "column_profiles": {
                    "X": {"data_type": "integer"},
                    "Y": {"data_type": "integer"},
                }
            },
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "detected_anomalies" in findings
    assert "business_insights" in findings
    assert "validated_findings" in findings
    assert "analyst_recommendations" in findings

    # Should have flagged 1000.0 outlier in Y
    assert len(findings["detected_anomalies"]) == 1
    assert findings["detected_anomalies"][0]["affected_columns"] == ["Y"]
    assert "outlier" in findings["detected_anomalies"][0]["title"].lower()

    # Recommendations must contain outlier remediation advice
    assert len(findings["analyst_recommendations"]) >= 1
    assert any("Investigate data entry errors" in r for r in findings["analyst_recommendations"])

    # Verify agent memory tracked validations & decisions
    assert "Executed skepticism validation on computed statistical tests." in agent.memory.reasoning_history
    assert any("Rejected finding:" in f for f in agent.memory.accepted_findings)
    assert any("rejected_finding:" in ref for ref in agent.memory.evidence_references)
    assert any("Executed anomaly and insight extraction." in f for f in agent.memory.reasoning_history)
    assert any("Detected anomaly: Outliers Detected in Y" in f for f in agent.memory.accepted_findings)

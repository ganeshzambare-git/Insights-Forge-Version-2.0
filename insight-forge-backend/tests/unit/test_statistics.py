"""
Insight Forge V2 — Unit Tests for Statistical Analysis & Trend Detection.

Validates Pearson correlation, linear regression, Chi-Square, ANOVA,
selection rules on empty/mixed datasets, and analyst integration.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIDataAnalyst,
    KPIMetadata,
    BusinessQuestion,
    AnalystLLMResponse,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.utils.statistics import (
    calculate_pearson,
    calculate_linear_regression,
    calculate_chi_square_independence,
    calculate_anova,
    detect_trends_and_change_points,
    run_statistical_analysis,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider returning static analyst response models."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        if schema is AnalystLLMResponse:
            return AnalystLLMResponse(
                discovered_kpis=[
                    KPIMetadata(
                        kpi_name="Sales",
                        description="Revenue summation",
                        required_columns=["Revenue"],
                        aggregation_type="SUM",
                        business_purpose="Determine volume",
                        confidence=0.9,
                    )
                ],
                business_questions=[
                    BusinessQuestion(
                        question_text="Why do sales grow?",
                        priority="High",
                        confidence=0.9,
                        required_columns=["Revenue"],
                        reasoning="Sales optimization",
                    )
                ],
                overall_confidence=0.95,
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


def test_pearson_correlation() -> None:
    """Verify Pearson correlation coefficient calculations."""
    x = [1.0, 2.0, 3.0, 4.0]
    y = [2.0, 4.0, 6.0, 8.0]
    r, p = calculate_pearson(x, y)
    assert r == pytest.approx(1.0)
    assert p == pytest.approx(0.0)

    # Inverse correlation
    y_inv = [8.0, 6.0, 4.0, 2.0]
    r_inv, p_inv = calculate_pearson(x, y_inv)
    assert r_inv == pytest.approx(-1.0)

    # No variance fallback
    flat_x = [1.0, 1.0, 1.0, 1.0]
    r_flat, p_flat = calculate_pearson(flat_x, y)
    assert r_flat == 0.0
    assert p_flat == 1.0


def test_linear_regression() -> None:
    """Verify linear regression slope, intercept, and determination coefficient."""
    x = [1.0, 2.0, 3.0, 4.0]
    y = [3.0, 5.0, 7.0, 9.0]
    slope, intercept, r2, p = calculate_linear_regression(x, y)
    assert slope == pytest.approx(2.0)
    assert intercept == pytest.approx(1.0)
    assert r2 == pytest.approx(1.0)


def test_chi_square_independence() -> None:
    """Verify Chi-Square calculation for categorical independence."""
    # Completely dependent
    x = ["A", "A", "B", "B"]
    y = ["X", "X", "Y", "Y"]
    chi, p = calculate_chi_square_independence(x, y)
    assert chi > 0.0
    assert p < 0.05

    # Independent/flat check
    x_flat = ["A", "A", "A", "A"]
    chi_flat, p_flat = calculate_chi_square_independence(x_flat, y)
    assert chi_flat == 0.0
    assert p_flat == 1.0


def test_anova() -> None:
    """Verify single-factor ANOVA calculations."""
    g1 = [10.0, 12.0, 11.0]
    g2 = [100.0, 105.0, 102.0]
    f_stat, p = calculate_anova([g1, g2])
    assert f_stat > 10.0
    assert p < 0.01


def test_trend_and_change_point_detection() -> None:
    """Verify temporal trend detection, growth, moving average, and least-square splits."""
    series = [10.0, 12.0, 14.0, 16.0, 100.0, 105.0, 110.0, 115.0]
    res = detect_trends_and_change_points(series)

    assert res["growth_rate"] == pytest.approx(10.5)  # (115 - 10) / 10 = 10.5
    assert len(res["moving_averages"]) == 6  # 8 - 3 + 1 = 6 items
    assert res["change_point_index"] == 4  # mean shifts from ~13 to ~107 at index 4


def test_statistical_selection_rules_and_fallbacks() -> None:
    """Verify automated analysis selection ignores strings in numeric columns and handles boundaries."""
    # 1. Empty dataset validation
    empty_summary = run_statistical_analysis([], {"col": "integer"})
    assert len(empty_summary.warnings) == 1
    assert "insufficient" in empty_summary.warnings[0].lower()

    # 2. Mixed type validation (strings in integer column)
    mixed_data = [
        {"num": 10, "cat": "X"},
        {"num": "corrupted", "cat": "Y"},
        {"num": 30, "cat": "X"},
    ]
    mixed_summary = run_statistical_analysis(mixed_data, {"num": "integer", "cat": "string"})
    # Since 'num' is corrupted, it should be ignored for numeric tests (no correlations or trends)
    assert len(mixed_summary.correlations) == 0
    assert len(mixed_summary.trends) == 0


@pytest.mark.asyncio
async def test_analyst_statistical_integration_and_validation() -> None:
    """Verify AIDataAnalyst execute integrates statistical engine and flags Data Engineer mismatches."""
    llm = MockLLMProvider()
    agent = AIDataAnalyst(name="test-analyst", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-stats-1",
        dataset_metadata={
            "dataset_name": "performance_records",
            "columns": ["X", "Y", "C"],
            "sample_rows": [
                {"X": 1, "Y": 2, "C": "bad_type"},  # C is numeric, but has string 'bad_type'
                {"X": 2, "Y": 4, "C": 10.5},
                {"X": 3, "Y": 6, "C": 12.0},
                {"X": 4, "Y": 8, "C": 14.5},
                {"X": 5, "Y": 10, "C": 16.0},
            ],
            "dataset_profile": {
                "column_profiles": {
                    "X": {"data_type": "integer"},
                    "Y": {"data_type": "integer"},
                    "C": {"data_type": "float"},  # Data Engineer says C is float
                }
            },
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "statistical_results" in findings
    assert "trend_analysis" in findings
    assert "correlation_results" in findings
    assert "analyst_evidence" in findings

    # X vs Y correlation should be 1.0 (since Y = 2*X)
    corr = findings["correlation_results"][0]
    assert corr["target_columns"] == ["X", "Y"]
    assert corr["correlation_coefficient"] == pytest.approx(1.0)

    # Verify that Analyst verified and flagged C classification mismatch in memory
    assert any("Data Engineer classification mismatch" in f for f in agent.memory.accepted_findings)
    assert any("Validation Warning:" in f for f in agent.memory.accepted_findings)
    # C should have been overridden to string, so no X vs C or Y vs C correlations were run
    assert len(findings["correlation_results"]) == 1  # only X vs Y correlation

    # Verify that memory logged statistical items
    assert "Executed automated statistical engine." in agent.memory.reasoning_history
    assert any("Discovered correlation: 1.0000 between ['X', 'Y']" in f for f in agent.memory.accepted_findings)

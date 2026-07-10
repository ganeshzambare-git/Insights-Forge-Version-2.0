"""
Insight Forge V2 — Unit Tests for AI Data Analyst.

Validates input validation checks, KPI discovery, business question extraction,
structured metadata output matching, and memory updates.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AIValidationError,
    AgentContractResponse,
    AIDataAnalyst,
    KPIMetadata,
    BusinessQuestion,
    AnalystLLMResponse,
)
from app.ai.llm.provider import BaseLLMProvider


class MockAnalystLLMProvider(BaseLLMProvider):
    """Mock implementation returning AnalystLLMResponse schemas for business metrics testing."""

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
                        kpi_name="Total Revenue",
                        description="Aggregated income from quantity sold and unit price.",
                        required_columns=["Qty", "Price"],
                        aggregation_type="SUM",
                        business_purpose="Determine overall sales volume and profit margins.",
                        confidence=0.98,
                    ),
                    KPIMetadata(
                        kpi_name="Average Unit Price",
                        description="Mean price points across transacted items.",
                        required_columns=["Price"],
                        aggregation_type="AVG",
                        business_purpose="Understand price pricing variations over time.",
                        confidence=0.94,
                    ),
                ],
                business_questions=[
                    BusinessQuestion(
                        question_text="Which products generate the highest revenue?",
                        priority="High",
                        confidence=0.95,
                        required_columns=["ProductID", "Qty", "Price"],
                        reasoning="Allows prioritization of high-value inventory lines.",
                    ),
                    BusinessQuestion(
                        question_text="How has total sales volume trended over dates?",
                        priority="Medium",
                        confidence=0.88,
                        required_columns=["OrderDate", "Qty"],
                        reasoning="Pinpoints seasonal demand cycles.",
                    ),
                ],
                overall_confidence=0.95,
                warnings=["Missing CustomerID field prevents customer segment cohort mapping."],
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


def test_analyst_input_validation() -> None:
    """Verify AIDataAnalyst validate_input raises ValidationError on missing dataset details."""
    llm = MockAnalystLLMProvider()
    agent = AIDataAnalyst(name="test-analyst", llm_provider=llm)

    # 1. Missing dataset_metadata dict
    context_no_meta = AIContext(tenant_id="tenant-analyst-1")
    with pytest.raises(AIValidationError, match="Missing dataset_metadata"):
        import asyncio
        asyncio.run(agent.validate_input(context_no_meta))

    # 2. Empty columns list
    context_no_cols = AIContext(
        tenant_id="tenant-analyst-1",
        dataset_metadata={"dataset_name": "sales_records", "columns": []},
    )
    with pytest.raises(AIValidationError, match="Missing or empty 'columns' list"):
        asyncio.run(agent.validate_input(context_no_cols))

    # 3. Missing dataset name
    context_no_name = AIContext(
        tenant_id="tenant-analyst-1",
        dataset_metadata={"dataset_name": "", "columns": ["Qty"]},
    )
    with pytest.raises(AIValidationError, match="Missing 'dataset_name'"):
        asyncio.run(agent.validate_input(context_no_name))


@pytest.mark.asyncio
async def test_analyst_kpi_and_question_discovery() -> None:
    """Verify end-to-end execution of AIDataAnalyst mapping metrics, questions, and evidence."""
    llm = MockAnalystLLMProvider()
    agent = AIDataAnalyst(name="test-analyst", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-analyst-1",
        dataset_metadata={
            "dataset_name": "retail_orders_summary",
            "columns": ["ProductID", "Qty", "Price", "OrderDate"],
            "dataset_profile": {
                "overall_quality_score": 0.95,
                "column_profiles": {
                    "Qty": {"data_type": "integer", "null_count": 0},
                    "Price": {"data_type": "float", "null_count": 0},
                },
            },
            "dataset_summary": {
                "overall_quality_score": 0.95,
                "total_issues_detected": 0,
                "certification_status": "Certified",
            },
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "discovered_kpis" in findings
    assert "business_questions" in findings
    assert "kpi_metadata" in findings
    assert findings["confidence"] == 0.95
    assert "Missing CustomerID field prevents customer segment cohort mapping." in findings["warnings"]

    # Verify discovered KPI details
    kpis = findings["discovered_kpis"]
    assert len(kpis) == 2
    assert kpis[0]["kpi_name"] == "Total Revenue"
    assert kpis[0]["aggregation_type"] == "SUM"
    assert kpis[0]["required_columns"] == ["Qty", "Price"]

    # Verify generated business questions
    questions = findings["business_questions"]
    assert len(questions) == 2
    assert questions[0]["question_text"] == "Which products generate the highest revenue?"
    assert questions[0]["priority"] == "High"
    assert questions[0]["reasoning"] == "Allows prioritization of high-value inventory lines."

    # Verify metadata mappings
    assert "Total Revenue" in findings["kpi_metadata"]
    assert "Average Unit Price" in findings["kpi_metadata"]

    # Verify traceability evidence has been collected
    assert len(response.evidence) == 4  # 2 KPIs + 2 Business Questions
    assert response.evidence[0].source == "kpi:Total Revenue"
    assert response.evidence[0].supporting_columns == ["Qty", "Price"]
    assert response.evidence[2].source == "question:Which products generate the highest revenue?"
    assert response.evidence[2].supporting_columns == ["ProductID", "Qty", "Price"]

    # Verify Agent Memory logs
    assert "Discovered KPI: Total Revenue" in agent.memory.accepted_findings
    assert "Generated business question: Which products generate the highest revenue?" in agent.memory.accepted_findings
    assert "Mapped KPI 'Total Revenue' using columns ['Qty', 'Price']" in agent.memory.reasoning_history
    assert "overall_confidence" in [list(d.keys())[0] for d in agent.memory.execution_memory]
    assert "kpi:Total Revenue:column:Qty" in agent.memory.evidence_references

"""
Insight Forge V2 — Unit Tests for AI Data Engineer.

Validates input validation, prompt rendering, semantic column inference,
column classification, memory populating, and structured metadata output.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AIValidationError,
    AgentContractResponse,
    AIDataEngineer,
)
from app.ai.agents.data_engineer import (
    ColumnUnderstandingItem,
    DatasetUnderstandingLLMResponse,
)
from app.ai.llm.provider import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock implementation of BaseLLMProvider returning deterministic schemas for testing."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        if schema is DatasetUnderstandingLLMResponse:
            return DatasetUnderstandingLLMResponse(
                estimated_industry="Education Technology",
                estimated_business_domain="Student Management",
                estimated_business_process="Cohort Performance Monitoring",
                row_representation="A single student enrollment record with academic metrics.",
                detected_entities=["Student", "Cohort", "Instructor"],
                columns=[
                    ColumnUnderstandingItem(
                        column_name="Cust_ID",
                        business_meaning="Customer Identifier",
                        classification="Identifier",
                        confidence=0.99,
                        reasoning="Standard id abbreviation",
                        evidence="Ends with ID suffix",
                    ),
                    ColumnUnderstandingItem(
                        column_name="Qty",
                        business_meaning="Quantity Sold",
                        classification="Measure",
                        confidence=0.95,
                        reasoning="Represents quantity amount",
                        evidence="Numeric count integer values",
                    ),
                    ColumnUnderstandingItem(
                        column_name="Amt",
                        business_meaning="Revenue Amount",
                        classification="Financial",
                        confidence=0.97,
                        reasoning="Abbreviation for amount, associated with currency",
                        evidence="Floating point with currency symbol",
                    ),
                    ColumnUnderstandingItem(
                        column_name="DOB",
                        business_meaning="Date of Birth",
                        classification="Timestamp",
                        confidence=1.0,
                        reasoning="Acronym for Date of Birth",
                        evidence="YYYY-MM-DD format match",
                    ),
                    ColumnUnderstandingItem(
                        column_name="ShipDt",
                        business_meaning="Shipping Date",
                        classification="Timestamp",
                        confidence=0.92,
                        reasoning="Shorthand for Ship Date",
                        evidence="Date stamps present in fields",
                    ),
                ],
                overall_confidence=0.96,
                assumptions=["Assuming Cust_ID maps to student index in this context."],
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


@pytest.mark.asyncio
async def test_data_engineer_validation_failures() -> None:
    """Verify input validation fails on missing columns or dataset_name."""
    llm = MockLLMProvider()
    agent = AIDataEngineer(name="test-engineer", llm_provider=llm)

    # Missing metadata entirely
    context_empty = AIContext(tenant_id="t1")
    with pytest.raises(AIValidationError) as exc:
        await agent.execute(context_empty)
    assert "dataset_metadata" in str(exc.value)

    # Missing dataset_name
    context_no_name = AIContext(
        tenant_id="t1",
        dataset_metadata={
            "columns": ["Cust_ID", "Qty"],
        },
    )
    with pytest.raises(AIValidationError) as exc:
        await agent.execute(context_no_name)
    assert "dataset_name" in str(exc.value)

    # Missing columns list
    context_no_cols = AIContext(
        tenant_id="t1",
        dataset_metadata={
            "dataset_name": "Students",
        },
    )
    with pytest.raises(AIValidationError) as exc:
        await agent.execute(context_no_cols)
    assert "columns" in str(exc.value)


@pytest.mark.asyncio
async def test_data_engineer_successful_understanding() -> None:
    """Verify success run, semantic column checks, classifications, metadata, and memory."""
    llm = MockLLMProvider()
    agent = AIDataEngineer(name="test-engineer", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-edu-1",
        dataset_metadata={
            "dataset_name": "student_enrollment_records",
            "columns": ["Cust_ID", "Qty", "Amt", "DOB", "ShipDt"],
            "sample_rows": [
                {"Cust_ID": "C-12", "Qty": "1", "Amt": "$100", "DOB": "2000-01-01", "ShipDt": "2023-01-01"}
            ],
            "row_count": 1050,
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True
    assert response.agent_name == "test-engineer"

    findings = response.findings
    assert findings["estimated_industry"] == "Education Technology"
    assert findings["estimated_business_domain"] == "Student Management"
    assert findings["estimated_business_process"] == "Cohort Performance Monitoring"
    assert findings["row_representation"] == "A single student enrollment record with academic metrics."
    assert findings["detected_entities"] == ["Student", "Cohort", "Instructor"]

    # Semantic columns mapping check
    cols_und = findings["columns_understanding"]
    assert cols_und["Cust_ID"]["business_meaning"] == "Customer Identifier"
    assert cols_und["Qty"]["business_meaning"] == "Quantity Sold"
    assert cols_und["Amt"]["business_meaning"] == "Revenue Amount"
    assert cols_und["DOB"]["business_meaning"] == "Date of Birth"
    assert cols_und["ShipDt"]["business_meaning"] == "Shipping Date"

    # Columns classifications checks
    assert cols_und["Cust_ID"]["classification"] == "Identifier"
    assert cols_und["Qty"]["classification"] == "Measure"
    assert cols_und["Amt"]["classification"] == "Financial"
    assert cols_und["DOB"]["classification"] == "Timestamp"
    assert cols_und["ShipDt"]["classification"] == "Timestamp"

    # Evidence details check
    assert len(response.evidence) == 18
    assert response.evidence[0].source == "column:Cust_ID"
    assert response.evidence[0].supporting_columns == ["Cust_ID"]
    assert response.evidence[0].confidence == 0.99
    assert response.evidence[0].validation_status == "CONFIRMED"

    # Structured metadata check
    meta = findings["metadata"]
    assert meta["dataset_name"] == "student_enrollment_records"
    assert meta["row_count"] == 1050
    assert meta["column_count"] == 5
    assert meta["estimated_industry"] == "Education Technology"
    assert meta["estimated_business_domain"] == "Student Management"
    assert meta["detected_entities"] == ["Student", "Cohort", "Instructor"]
    
    # Check that classifications match lists in metadata
    assert "Qty" in meta["detected_measures"]
    assert "Amt" in meta["detected_measures"]  # Financial mapped as measure in metadata
    assert "Cust_ID" in meta["detected_identifiers"]
    assert "DOB" in meta["detected_timestamp_columns"]
    assert "ShipDt" in meta["detected_timestamp_columns"]

    # Memory state tracking verification
    assert len(agent.memory.reasoning_history) > 0
    assert "Mapped 'Cust_ID' to business concept 'Customer Identifier'" in agent.memory.reasoning_history
    assert "Classified 'Cust_ID' as a 'Identifier'" in agent.memory.reasoning_history
    assert "Detected business entity: Student" in agent.memory.accepted_findings
    assert "Hypothesis Confirmed: Assumption: Assuming Cust_ID maps to student index in this context." in agent.memory.accepted_findings
    assert {"overall_confidence": 0.96} in agent.memory.execution_memory

"""
Insight Forge V2 — Unit Tests for Professional Data Profiling.

Validates entropy, standard deviation, quality scoring, constraint discovery,
validation of mixed/empty types, and memory loading.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIDataEngineer,
    ColumnProfile,
    DatasetProfile,
)
from app.ai.agents.data_engineer import (
    ColumnUnderstandingItem,
    DatasetUnderstandingLLMResponse,
)
from app.ai.utils.profiler import calculate_entropy, profile_dataset
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


def test_entropy_calculations() -> None:
    """Verify Shannon entropy calculations for distinct probability distributions."""
    # Constant values -> 0 entropy
    assert calculate_entropy([1, 1, 1, 1]) == 0.0
    assert calculate_entropy([]) == 0.0

    # 4 distinct values -> log2(4) = 2.0 entropy
    assert calculate_entropy([1, 2, 3, 4]) == pytest.approx(2.0)

    # Mixed float/string values
    assert calculate_entropy(["a", "b", "a", "b"]) == pytest.approx(1.0)


def test_column_profiling_calculations() -> None:
    """Verify statistics (mean, median, mode, std_dev) and length calculations."""
    data = [
        {"val": 10, "text": "cat"},
        {"val": 20, "text": "mouse"},
        {"val": 30, "text": "elephant"},
        {"val": None, "text": ""},  # null/missing row
    ]
    columns = ["val", "text"]

    profile: DatasetProfile = profile_dataset(data, columns, "TestTable")
    assert profile.row_count == 4
    assert profile.column_count == 2
    assert profile.overall_quality_score == pytest.approx(0.75)  # both columns have 0.75 quality due to 1 missing/empty value

    # val column stats check
    val_p: ColumnProfile = profile.column_profiles["val"]
    assert val_p.data_type == "integer"
    assert val_p.null_count == 1
    assert val_p.null_percentage == 0.25
    assert val_p.cardinality == 3
    assert val_p.min_value == 10.0
    assert val_p.max_value == 30.0
    assert val_p.mean == 20.0
    assert val_p.median == 20.0
    # population variance of [10, 20, 30] is 66.666 -> std_dev is ~8.165
    assert val_p.std_dev == pytest.approx(8.1649658)

    # text column length checks
    text_p: ColumnProfile = profile.column_profiles["text"]
    assert text_p.data_type == "string"
    assert text_p.length_min == 3
    assert text_p.length_max == 8
    assert text_p.length_mean == pytest.approx(16/3)  # lengths of ["cat", "mouse", "elephant"] are [3, 5, 8] -> avg 5.33


def test_constraint_discovery() -> None:
    """Verify identification of PKs, constant fields, nullable values, and pattern matches."""
    data = [
        {"pk": 1, "const": "fixed", "email": "a@b.com", "nulls": 10.5},
        {"pk": 2, "const": "fixed", "email": "a@b.com", "nulls": None},
        {"pk": 3, "const": "fixed", "email": "foo@bar.org", "nulls": 12.0},
    ]
    columns = ["pk", "const", "email", "nulls"]

    profile: DatasetProfile = profile_dataset(data, columns, "InferenceTable")
    constraints = {c.constraint_type: c for c in profile.constraints}

    # PK Candidate Check
    assert "PRIMARY_KEY" in constraints
    assert constraints["PRIMARY_KEY"].columns == ["pk"]
    assert constraints["PRIMARY_KEY"].confidence >= 0.8

    # Constant Check
    assert "CONSTANT" in constraints
    assert constraints["CONSTANT"].columns == ["const"]

    # Nullable Check
    assert "NULLABLE" in constraints
    assert constraints["NULLABLE"].columns == ["nulls"]

    # Pattern consistency Check
    assert "PATTERN" in constraints
    assert constraints["PATTERN"].columns == ["email"]


def test_profiler_edge_cases_and_validation() -> None:
    """Verify empty datasets, mixed datatypes, and high-cardinality collections handle safely."""
    # 1. Empty dataset validation
    profile_empty = profile_dataset([], ["col1"], "EmptyTable")
    assert profile_empty.row_count == 0
    assert len(profile_empty.warnings) == 1
    assert "empty" in profile_empty.warnings[0].lower()
    assert profile_empty.column_profiles["col1"].unique_values_count == 0

    # 2. Mixed data types validation
    mixed_data = [
        {"mixed": 10},
        {"mixed": "non-numeric"},
        {"mixed": 20.5},
    ]
    profile_mixed = profile_dataset(mixed_data, ["mixed"], "MixedTable")
    assert profile_mixed.column_profiles["mixed"].data_type == "string"  # inferred string due to mixed fields
    # numeric stats should still try to calculate over castable numbers (10 and 20.5)
    assert profile_mixed.column_profiles["mixed"].mean == pytest.approx(15.25)
    # Check that mixed warning is present in profile
    assert any("Mixed data types" in w for w in profile_mixed.warnings)

    # 3. High-cardinality capping validation
    high_card_data = [{"card": i} for i in range(100)]
    profile_high_card = profile_dataset(high_card_data, ["card"], "HighCardTable")
    assert len(profile_high_card.column_profiles["card"].value_distribution) == 10  # Capped at top 10 values


@pytest.mark.asyncio
async def test_data_engineer_agent_profiling_integration() -> None:
    """Verify end-to-end AIDataEngineer execution with profiling data."""
    llm = MockLLMProvider()
    agent = AIDataEngineer(name="test-engineer", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-profiling-1",
        dataset_metadata={
            "dataset_name": "cohort_performance_data",
            "columns": ["Cust_ID", "Qty", "Amt", "DOB", "ShipDt"],
            "sample_rows": [
                {"Cust_ID": "C101", "Qty": 10, "Amt": "$100", "DOB": "2000-01-01", "ShipDt": "2023-01-01"},
                {"Cust_ID": "C102", "Qty": 20, "Amt": "$200", "DOB": "2001-02-02", "ShipDt": "2023-01-02"},
                {"Cust_ID": "C103", "Qty": 30, "Amt": "$300", "DOB": "2002-03-03", "ShipDt": "2023-01-03"},
            ],
            "row_count": 3,
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "dataset_profile" in findings
    assert "column_profiles" in findings
    assert "quality_metrics" in findings
    assert "constraint_analysis" in findings
    assert "profiling_summary" in findings

    # Verify overall quality calculation
    assert findings["quality_metrics"]["overall_quality_score"] == 1.0  # clean, no nulls

    # Verify memory tracks constraints and history
    assert "Executed professional data profiling." in agent.memory.reasoning_history
    assert "Dataset Quality Score: 1.0" in agent.memory.accepted_findings
    assert any("Discovered constraint: PRIMARY_KEY on ['Cust_ID']" in f for f in agent.memory.accepted_findings)
    assert "constraint:PRIMARY_KEY:Cust_ID" in agent.memory.evidence_references
    assert any("profiling_quality_score" in record for record in agent.memory.execution_memory)

"""
Insight Forge V2 — Unit Tests for Intelligent Data Cleaning.

Validates issue detection, cleaning recommendations, certification mapping tiers,
empty validation safety, and memory log generation.
"""

from typing import Any
import pytest
from pydantic import BaseModel

from app.ai import (
    AIContext,
    AgentContractResponse,
    AIDataEngineer,
)
from app.ai.agents.data_engineer import (
    ColumnUnderstandingItem,
    DatasetUnderstandingLLMResponse,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.utils.cleaning import generate_trusted_dataset, map_certification


class MockLLMProvider(BaseLLMProvider):
    """Mock implementation returning schemas for data engineer runs."""

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
                estimated_industry="Retail Commerce",
                estimated_business_domain="Sales Operations",
                estimated_business_process="Order Management",
                row_representation="A single sales transaction line item.",
                detected_entities=["Customer", "Order", "Product"],
                columns=[
                    ColumnUnderstandingItem(
                        column_name="OrderID",
                        business_meaning="Order Identifier",
                        classification="Identifier",
                        confidence=0.98,
                        reasoning="Unique key",
                        evidence="Header ends with ID",
                    ),
                    ColumnUnderstandingItem(
                        column_name="Email",
                        business_meaning="Customer Email Address",
                        classification="Dimension",
                        confidence=0.97,
                        reasoning="Contains contact info",
                        evidence="Contains text matching standard structure",
                    ),
                    ColumnUnderstandingItem(
                        column_name="Qty",
                        business_meaning="Quantity",
                        classification="Measure",
                        confidence=0.95,
                        reasoning="Numeric amount",
                        evidence="Number values",
                    ),
                ],
                overall_confidence=0.96,
                assumptions=["Assuming OrderID is unique per row."],
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


def test_certification_mapping_logic() -> None:
    """Verify quality score and critical counts map correctly to certification tiers."""
    # 1. Certified
    assert map_certification(0.98, total_issues=0, critical_issues=0) == "Certified"

    # 2. Certified with Warnings
    assert map_certification(0.92, total_issues=2, critical_issues=0) == "Certified with Warnings"

    # 3. Requires Review
    assert map_certification(0.75, total_issues=5, critical_issues=0) == "Requires Review"
    assert map_certification(0.95, total_issues=3, critical_issues=1) == "Requires Review"

    # 4. Not Certified
    assert map_certification(0.55, total_issues=10, critical_issues=0) == "Not Certified"
    assert map_certification(0.85, total_issues=12, critical_issues=4) == "Not Certified"


def test_data_issue_detections() -> None:
    """Verify detection of whitespaces, casing, invalid emails, negative bounds, and duplicates."""
    data = [
        {"OrderID": "O-100", "Email": "alice@bob.com", "Qty": 10},
        {"OrderID": "O-100", "Email": "alice@bob.com", "Qty": 10},  # duplicate row
        {"OrderID": "O-102", "Email": "bad_email_format", "Qty": -5},  # invalid email and out-of-range qty
        {"OrderID": "  O-103  ", "Email": "test@domain.com", "Qty": 20},  # whitespace issue
        {"OrderID": "O-104", "Email": "ACTIVE@DOMAIN.COM", "Qty": 30},
        {"OrderID": "O-105", "Email": "active@domain.com", "Qty": 40},  # casing variations
    ]
    columns = ["OrderID", "Email", "Qty"]

    summary, log = generate_trusted_dataset(data, columns, "DirtyOrders")
    recommendations = {r.issue_type: r for r in summary.cleaning_recommendations}

    # Verify duplicate rows recommendation
    assert "DUPLICATE_ROWS" in recommendations
    assert recommendations["DUPLICATE_ROWS"].recommended_action == "Remove duplicates"

    # Verify duplicate identifiers on OrderID
    assert "DUPLICATE_IDENTIFIERS" in recommendations
    assert recommendations["DUPLICATE_IDENTIFIERS"].severity == "Critical"
    assert recommendations["DUPLICATE_IDENTIFIERS"].recommended_action == "Flag for manual review"

    # Verify whitespace on OrderID
    assert "WHITESPACE_ISSUES" in recommendations
    assert recommendations["WHITESPACE_ISSUES"].severity == "Low"

    # Verify invalid email on Email
    assert "INVALID_EMAIL_FORMAT" in recommendations
    assert recommendations["INVALID_EMAIL_FORMAT"].severity == "High"

    # Verify out-of-range on Qty
    assert "OUT_OF_RANGE_VALUES" in recommendations
    assert recommendations["OUT_OF_RANGE_VALUES"].severity == "High"

    # Verify casing inconsistencies on Email column
    assert "CASING_INCONSISTENCY" in recommendations
    assert recommendations["CASING_INCONSISTENCY"].recommended_action == "Normalize categories"


def test_cleaner_empty_dataset_safety() -> None:
    """Verify empty datasets do not cause crashes and default to Not Certified."""
    summary, log = generate_trusted_dataset([], ["OrderID"], "EmptyTable")
    assert summary.overall_quality_score == 0.0
    assert summary.total_issues_detected == 0
    assert summary.certification_status == "Not Certified"
    assert len(log) == 0


@pytest.mark.asyncio
async def test_data_engineer_cleaning_integration() -> None:
    """Verify AIDataEngineer execute compiles dataset summaries and logs decisions in memory."""
    llm = MockLLMProvider()
    agent = AIDataEngineer(name="test-engineer", llm_provider=llm)

    context = AIContext(
        tenant_id="tenant-cleaning-1",
        dataset_metadata={
            "dataset_name": "dirty_transactions_data",
            "columns": ["OrderID", "Email", "Qty"],
            "sample_rows": [
                {"OrderID": "  T1  ", "Email": "john@doe.com", "Qty": 10},
                {"OrderID": "  T1  ", "Email": "john@doe.com", "Qty": 10},  # duplicate row
                {"OrderID": "T2", "Email": "bad-email", "Qty": -20},  # high severity errors
            ],
            "row_count": 3,
        },
    )

    response = await agent.execute(context)
    assert isinstance(response, AgentContractResponse)
    assert response.success is True

    findings = response.findings
    assert "dataset_summary" in findings
    assert "cleaning_log" in findings
    assert "certification_status" in findings

    # Should have flagged issues due to duplicate rows, negative values, and invalid email
    assert findings["dataset_summary"]["total_issues_detected"] == 5
    assert findings["dataset_summary"]["critical_issues_count"] == 1  # OrderID duplicates

    # Certification must be Requires Review due to critical duplicate identifier and out-of-range qty
    assert findings["certification_status"] == "Requires Review"

    # Verify memory tracks cleaning decisions
    assert "Executed intelligent data cleaning analysis." in agent.memory.reasoning_history
    assert any("Proposed cleaning action:" in f for f in agent.memory.accepted_findings)
    assert any("cleaning_log_evidence" in ref for ref in agent.memory.evidence_references)
    assert any("certification_history" in record for record in agent.memory.execution_memory)

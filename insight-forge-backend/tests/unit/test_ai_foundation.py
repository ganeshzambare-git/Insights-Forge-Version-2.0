"""
Insight Forge V2 — Unit Tests for AI Foundation.

Validates schemas, immutable context evolution, prompt management, base agent execution lifecycle, and utilities.
"""

from typing import Any
import pytest
from pydantic import ValidationError

from app.ai import (
    AIContext,
    AIValidationError,
    ConfidenceModel,
    Evidence,
    BaseAIAgent,
    AgentContractResponse,
    AgentMemory,
    PromptManager,
    PromptTemplate,
    PromptType,
    PromptError,
    AIError,
)
from app.ai.utils.helpers import (
    calculate_average_confidence,
    filter_evidence_by_status,
    map_score_to_categorical_level,
    safe_serialize_json,
)


def test_custom_exceptions() -> None:
    """Verify standard inheritance and properties of custom AI exceptions."""
    err = AIValidationError("Schema check failed", error_code="schema_err")
    assert isinstance(err, AIError)
    assert err.message == "Schema check failed"
    assert err.error_code == "schema_err"

    with pytest.raises(PromptError):
        raise PromptError("Rendering failure")


def test_confidence_model_constraints() -> None:
    """Verify confidence score limits ge=0.0 and le=1.0."""
    # Valid model
    model = ConfidenceModel(
        confidence_score=0.85,
        confidence_level="HIGH",
        explanation="Validated by query analysis",
        uncertainty="None",
        validation_status="VALIDATED",
    )
    assert model.confidence_score == 0.85

    # Invalid - negative score
    with pytest.raises(ValidationError):
        ConfidenceModel(
            confidence_score=-0.1,
            confidence_level="LOW",
            explanation="Invalid",
            uncertainty="None",
            validation_status="PENDING",
        )

    # Invalid - score > 1.0
    with pytest.raises(ValidationError):
        ConfidenceModel(
            confidence_score=1.2,
            confidence_level="HIGH",
            explanation="Too high",
            uncertainty="None",
            validation_status="PENDING",
        )


def test_evidence_model_defaults() -> None:
    """Verify evidence model default UUID generation and field values."""
    ev = Evidence(
        source="students_table",
        supporting_columns=["attendance_rate", "grades"],
        business_support="Correlates attendance with higher performance.",
        confidence=0.9,
    )
    assert ev.evidence_id is not None
    assert len(ev.evidence_id) > 0
    assert ev.validation_status == "PENDING"


def test_immutable_ai_context_evolution() -> None:
    """Verify immutability constraints of AIContext and evolution copies."""
    context = AIContext(tenant_id="tenant-101")
    assert context.tenant_id == "tenant-101"
    assert context.execution_status == "INITIALIZED"

    # Test frozen/immutable
    with pytest.raises(ValidationError):
        # In Pydantic v2, setting attribute raises ValidationError (or AttributeError in some cases, Pydantic raises ValidationError for frozen fields)
        context.execution_status = "RUNNING"  # type: ignore

    # Test evolution
    new_context = context.evolve(execution_status="IN_PROGRESS", warnings=["First Warning"])
    assert new_context is not context
    assert new_context.tenant_id == "tenant-101"
    assert new_context.execution_status == "IN_PROGRESS"
    assert new_context.warnings == ["First Warning"]


def test_prompt_manager_and_rendering() -> None:
    """Verify PromptTemplate parameter check validation and registration key retrieval."""
    manager = PromptManager()
    template = PromptTemplate(
        name="test_prompt",
        version="1.0.0",
        template_str="Hello {name}, welcome to {platform}!",
        prompt_type=PromptType.USER,
        required_variables=["name", "platform"],
    )

    manager.register(template)

    # Valid rendering
    rendered = manager.render("test_prompt", "1.0.0", name="Alice", platform="InsightForge")
    assert rendered == "Hello Alice, welcome to InsightForge!"

    # Missing parameter
    with pytest.raises(PromptError) as exc_info:
        manager.render("test_prompt", "1.0.0", name="Alice")
    assert "missing" in str(exc_info.value)

    # Missing registry item
    with pytest.raises(PromptError) as exc_info:
        manager.get("unknown_prompt", "1.0.0")
    assert "not registered" in str(exc_info.value)


class MockAgent(BaseAIAgent):
    """Concrete mock agent subclass to validate execution templates."""

    async def validate_input(self, context: AIContext, *args: Any, **kwargs: Any) -> None:
        if "test_key" not in kwargs:
            raise AIValidationError("Missing test_key in kwargs")

    async def validate_output(
        self, context: AIContext, response: AgentContractResponse
    ) -> None:
        if not response.success:
            raise AIValidationError("Response marked unsuccessful")

    async def generate_confidence(
        self, context: AIContext, findings: dict[str, Any]
    ) -> ConfidenceModel:
        return ConfidenceModel(
            confidence_score=0.95,
            confidence_level="HIGH",
            explanation="Mock execution high match",
            uncertainty="None",
            validation_status="VALIDATED",
        )

    async def collect_evidence(self, context: AIContext, findings: dict[str, Any]) -> list[Evidence]:
        return [
            Evidence(
                source="mock_test",
                supporting_columns=["test_col"],
                business_support="Supported by mock run context data.",
                confidence=0.95,
                validation_status="CONFIRMED",
            )
        ]

    async def produce_structured_response(
        self,
        context: AIContext,
        findings: dict[str, Any],
        confidence: ConfidenceModel,
        evidence: list[Evidence],
        errors: list[str],
    ) -> AgentContractResponse:
        return AgentContractResponse(
            success=len(errors) == 0,
            agent_name=self.name,
            findings=findings,
            confidence=confidence,
            evidence=evidence,
            errors=errors,
        )

    async def _run_analysis(self, context: AIContext, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"data_engineer_metric": kwargs["test_key"]}


@pytest.mark.asyncio
async def test_agent_lifecycle_pipeline() -> None:
    """Verify execution lifecycle template methods for abstract agents."""
    agent = MockAgent(name="mock-data-engineer")
    context = AIContext(tenant_id="tenant-xyz")

    # Run with missing keys to verify validation pre-conditions
    with pytest.raises(AIValidationError):
        await agent.execute(context)

    # Run successfully
    response = await agent.execute(context, test_key="value-xyz")
    assert isinstance(response, AgentContractResponse)
    assert response.success is True
    assert response.agent_name == "mock-data-engineer"
    assert response.findings == {"data_engineer_metric": "value-xyz"}
    assert response.confidence.confidence_score == 0.95
    assert len(response.evidence) == 1
    assert response.evidence[0].source == "mock_test"


def test_agent_memory_tracking() -> None:
    """Verify AIMemory tracking of history, findings, and hypotheses."""
    memory = AgentMemory()
    memory.add_reasoning_step("Initiating connection check.")
    memory.add_hypothesis("Missing values are concentrated in Attendance.", accepted=False)
    memory.add_hypothesis("Attendance correlates with higher final grades.", accepted=True)
    memory.add_finding("Final cohort GPA is 3.42.")
    memory.add_evidence_ref("ev-12345")
    memory.add_execution_record("model_param_x", 42)

    assert "Initiating connection check." in memory.reasoning_history
    assert "Missing values are concentrated in Attendance." in memory.rejected_hypotheses
    assert "Hypothesis Confirmed: Attendance correlates with higher final grades." in memory.accepted_findings
    assert "Final cohort GPA is 3.42." in memory.accepted_findings
    assert "ev-12345" in memory.evidence_references
    assert memory.execution_memory == [{"model_param_x": 42}]

    memory.clear()
    assert len(memory.reasoning_history) == 0
    assert len(memory.accepted_findings) == 0


def test_utility_helpers() -> None:
    """Verify average calculations and text/status mapping helper utilities."""
    c1 = ConfidenceModel(
        confidence_score=0.8,
        confidence_level="HIGH",
        explanation="None",
        uncertainty="None",
        validation_status="PENDING",
    )
    c2 = ConfidenceModel(
        confidence_score=0.6,
        confidence_level="MEDIUM",
        explanation="None",
        uncertainty="None",
        validation_status="PENDING",
    )

    # Average confidence calculation
    avg = calculate_average_confidence([c1, c2])
    assert avg == pytest.approx(0.7)

    assert calculate_average_confidence([]) == 0.0

    # Categorical confidence score mapping
    assert map_score_to_categorical_level(0.85) == "HIGH"
    assert map_score_to_categorical_level(0.55) == "MEDIUM"
    assert map_score_to_categorical_level(0.2) == "LOW"

    # Evidence status filter
    ev1 = Evidence(source="s1", business_support="b1", confidence=0.8, validation_status="CONFIRMED")
    ev2 = Evidence(source="s2", business_support="b2", confidence=0.7, validation_status="PENDING")
    
    confirmed = filter_evidence_by_status([ev1, ev2], "confirmed")
    assert len(confirmed) == 1
    assert confirmed[0].source == "s1"

    # Safe serialization helper
    assert safe_serialize_json({"key": "val"}) == '{"key": "val"}'
    assert "s1" in safe_serialize_json(ev1)

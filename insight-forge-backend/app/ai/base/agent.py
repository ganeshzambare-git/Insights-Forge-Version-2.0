"""
Insight Forge V2 — Base AI Agent Class.

Implements the Template Method pattern defining execution lifecycles of AI agents.
"""

from abc import ABC, abstractmethod
from typing import Any
from app.ai.context.model import AIContext
from app.ai.contracts.agent import AgentContract, AgentContractResponse
from app.ai.evidence.model import Evidence
from app.ai.schemas.confidence import ConfidenceModel


class BaseAIAgent(AgentContract, ABC):
    """Abstract Base Class for all future AI professional agents.

    Provides a template method structure for initializing execution context,
    validating input/output parameters, scoring confidence, collecting evidence,
    and outputting strongly-typed responses.
    """

    def __init__(self, name: str) -> None:
        """Initialize base agent settings.

        Args:
            name: The unique machine name of the agent.
        """
        self.name = name

    async def initialize_context(self, context: AIContext) -> None:
        """Prepare context before agent execution starts.

        Override to register runtime timestamps, status states, etc.
        """
        pass

    @abstractmethod
    async def validate_input(self, context: AIContext, *args: Any, **kwargs: Any) -> None:
        """Validate context state, schemas, or requirements before agent runs.

        Raises:
            AIValidationError: If pre-conditions or configurations fail validation.
        """
        pass

    @abstractmethod
    async def validate_output(
        self, context: AIContext, response: AgentContractResponse
    ) -> None:
        """Verify the integrity, bounds, and correctness of produced findings.

        Raises:
            AIValidationError: If post-conditions or invariants fail validation.
        """
        pass

    @abstractmethod
    async def generate_confidence(
        self, context: AIContext, findings: dict[str, Any]
    ) -> ConfidenceModel:
        """Perform self-reflection or statistical calculation to yield confidence metrics.

        Args:
            context: Current execution context.
            findings: Generated raw findings.
        """
        pass

    @abstractmethod
    async def collect_evidence(self, context: AIContext, findings: dict[str, Any]) -> list[Evidence]:
        """Trace findings back to specific datasets, variables, or query metadata.

        Args:
            context: Current execution context.
            findings: Generated raw findings.
        """
        pass

    @abstractmethod
    async def produce_structured_response(
        self,
        context: AIContext,
        findings: dict[str, Any],
        confidence: ConfidenceModel,
        evidence: list[Evidence],
        errors: list[str],
    ) -> AgentContractResponse:
        """Wrap outcomes into a standardized AgentContractResponse object."""
        pass

    async def execute(self, context: AIContext, *args: Any, **kwargs: Any) -> AgentContractResponse:
        """Orchestrate the unified agent execution lifecycle flow.

        Follows Template Method pattern.
        """
        # Step 1: Initialize context hooks
        await self.initialize_context(context)

        # Step 2: Validate input requirements
        await self.validate_input(context, *args, **kwargs)

        errors: list[str] = []
        try:
            # Step 3: Run target execution pipeline
            findings = await self._run_analysis(context, *args, **kwargs)
        except Exception as e:
            # Keep trace of failure and package gracefully or bubble
            errors.append(f"Agent analysis failure: {str(e)}")
            raise

        # Step 4: Gather confidence scoring and evidence traces
        confidence = await self.generate_confidence(context, findings)
        evidence = await self.collect_evidence(context, findings)

        # Step 5: Format to contract structured response
        response = await self.produce_structured_response(
            context, findings, confidence, evidence, errors
        )

        # Step 6: Validate generated outputs/findings
        await self.validate_output(context, response)

        return response

    @abstractmethod
    async def _run_analysis(self, context: AIContext, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Subclass hook to implement actual agent reasoning loop and business rules."""
        pass

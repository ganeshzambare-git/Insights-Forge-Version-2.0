"""
Insight Forge V2 — AI Business Analyst Agent.

Implements automated 5 Whys root cause traceback analysis, competing hypothesis generation,
ranking, evidence verification, and strategic opportunity/ROI recommendation engines.
"""

from typing import Any

from app.ai.base.agent import BaseAIAgent
from app.ai.context.model import AIContext
from app.ai.contracts.agent import AgentContractResponse
from app.ai.evidence.model import Evidence
from app.ai.exceptions.custom import AIValidationError
from app.ai.llm.provider import BaseLLMProvider
from app.ai.memory.model import AgentMemory
from app.ai.prompts.manager import PromptManager, PromptTemplate, PromptType
from app.ai.schemas.confidence import ConfidenceModel
from app.ai.schemas.business import BusinessAnalysisSummary
from app.ai.schemas.strategy import StrategySummary
from app.ai.utils.helpers import map_score_to_categorical_level
from app.ai.utils.business import run_business_reasoning
from app.ai.utils.strategy import evaluate_strategy_recommendations


class AIBusinessAnalyst(BaseAIAgent):
    """AI Business Analyst agent.

    Responsible for operational root cause analysis (5 Whys), formulating competing business hypotheses,
    scoring and ranking explanations against data anomalies, and generating strategic business opportunities.
    """

    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        """Initialize the AI Business Analyst agent.

        Args:
            name: Machine name.
            llm_provider: The client wrapper for LLM requests.
            prompt_manager: Central manager to load versioned templates.
        """
        super().__init__(name)
        self.llm_provider = llm_provider
        self.prompt_manager = prompt_manager or PromptManager()
        self.memory = AgentMemory()

        self._register_default_prompts()

    def _register_default_prompts(self) -> None:
        """Register the system identity and user business templates."""
        # 1. Identity Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="BusinessAnalystIdentity",
                version="1.0.0",
                template_str=(
                    "You are the AI Business Analyst for InsightForge. Your job is to conduct "
                    "root cause analysis and formulate competing business hypotheses."
                ),
                prompt_type=PromptType.SYSTEM,
            )
        )

        # 2. Business Reasoning Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="BusinessReasoning",
                version="1.0.0",
                template_str=(
                    "Review the following context:\n"
                    "Dataset: {dataset_name}\n"
                    "Anomalies: {anomalies}\n"
                    "Insights: {insights}\n\n"
                    "Verify the validity of hypotheses and rank them."
                ),
                prompt_type=PromptType.USER,
                required_variables=["dataset_name", "anomalies", "insights"],
            )
        )

    async def validate_input(self, context: AIContext, *args: Any, **kwargs: Any) -> None:
        """Assert previous Analyst outputs or dataset metadata invariants are provided."""
        meta = context.dataset_metadata or {}
        anomalies = meta.get("detected_anomalies") or context.previous_outputs.get("detected_anomalies")
        insights = meta.get("business_insights") or context.previous_outputs.get("business_insights")

        if anomalies is None or insights is None:
            raise AIValidationError("Missing previous Data Analyst findings (detected_anomalies or business_insights) in context.")

    async def validate_output(
        self, context: AIContext, response: AgentContractResponse
    ) -> None:
        """Verify the structured response matches all API requirements."""
        if not response.success:
            raise AIValidationError(f"Business Analyst reasoning failed: {response.errors}")

        findings = response.findings
        required_keys = [
            "root_causes",
            "generated_hypotheses",
            "validated_hypotheses",
            "rejected_hypotheses",
            "business_reasoning",
        ]
        for key in required_keys:
            if key not in findings:
                raise AIValidationError(f"Output findings missing required key: '{key}'")

        # Extended validation for strategic recommendations outputs
        if "business_opportunities" in findings:
            strategy_keys = [
                "business_opportunities",
                "strategic_recommendations",
                "risks",
                "implementation_priorities",
            ]
            for key in strategy_keys:
                if key not in findings:
                    raise AIValidationError(f"Output findings missing strategic key: '{key}'")

    async def generate_confidence(
        self, context: AIContext, findings: dict[str, Any]
    ) -> ConfidenceModel:
        """Aggregate confidence scores from validated hypotheses."""
        validated = findings.get("validated_hypotheses", [])
        score = sum(h.get("confidence", 0.0) for h in validated) / max(len(validated), 1)
        level = map_score_to_categorical_level(score)
        return ConfidenceModel(
            confidence_score=score,
            confidence_level=level,
            explanation="Business Analyst confidence maps from verification score of accepted hypotheses.",
            uncertainty="Hypotheses validation depends on quality profile completeness.",
            validation_status="VALIDATED",
        )

    async def collect_evidence(self, context: AIContext, findings: dict[str, Any]) -> list[Evidence]:
        """Convert root causes, validated hypotheses, and strategy recommendations into audit evidence records."""
        evidences = []
        for rc in findings.get("root_causes", []):
            evidences.append(
                Evidence(
                    source=f"root_cause:{rc.get('title')}",
                    supporting_columns=rc.get("supporting_findings", []),
                    statistical_support={"confidence": rc.get("confidence")},
                    business_support=rc.get("business_impact", ""),
                    confidence=rc.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for h in findings.get("validated_hypotheses", []):
            evidences.append(
                Evidence(
                    source=f"hypothesis:{h.get('title')}",
                    supporting_columns=h.get("supporting_findings", []),
                    statistical_support={"confidence": h.get("confidence")},
                    business_support=h.get("business_impact", ""),
                    confidence=h.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        # Append evidence for opportunities and recommendations
        for o in findings.get("business_opportunities", []):
            evidences.append(
                Evidence(
                    source=f"opportunity:{o.get('title')}",
                    supporting_columns=[],
                    statistical_support={"confidence": o.get("confidence")},
                    business_support=o.get("business_impact", ""),
                    confidence=o.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for r in findings.get("strategic_recommendations", []):
            evidences.append(
                Evidence(
                    source=f"recommendation:{r.get('title')}",
                    supporting_columns=[],
                    statistical_support={"confidence": r.get("confidence")},
                    business_support=r.get("business_impact", ""),
                    confidence=r.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        return evidences

    async def produce_structured_response(
        self,
        context: AIContext,
        findings: dict[str, Any],
        confidence: ConfidenceModel,
        evidence: list[Evidence],
        errors: list[str],
    ) -> AgentContractResponse:
        """Construct conforming AgentContractResponse."""
        return AgentContractResponse(
            success=len(errors) == 0,
            agent_name=self.name,
            findings=findings,
            confidence=confidence,
            evidence=evidence,
            errors=errors,
        )

    async def _run_analysis(self, context: AIContext, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute business reasoning, backtracing anomalies, validating hypotheses, and forming strategic recommendations."""
        meta = context.dataset_metadata or {}
        anomalies = meta.get("detected_anomalies") or context.previous_outputs.get("detected_anomalies") or []
        insights = meta.get("business_insights") or context.previous_outputs.get("business_insights") or []
        validated_findings = meta.get("validated_findings") or context.previous_outputs.get("validated_findings") or []

        # 1. Clear memory before run
        self.memory.clear()

        # 2. Run pure Python business reasoning engine
        summary: BusinessAnalysisSummary = run_business_reasoning(
            anomalies, insights, validated_findings
        )

        # 3. Log findings, 5 Whys, and validation decisions into agent memory
        self.memory.add_reasoning_step("Initiated operational root cause analysis (5 Whys).")
        for rc in summary.root_causes:
            self.memory.add_finding(f"Root cause identified: {rc.title}")
            self.memory.add_evidence_ref(f"root_cause:{rc.title}")

        self.memory.add_reasoning_step("Initiated hypothesis validation against data quality anomalies.")
        for h in summary.validated_hypotheses:
            self.memory.add_finding(f"Validated hypothesis: {h.title} (Conf: {h.confidence:.4f})")
            self.memory.add_evidence_ref(f"validated_hyp:{h.title}")

        for hr in summary.rejected_hypotheses:
            self.memory.add_finding(f"Rejected hypothesis: {hr.title} - Rationale: {hr.evidence}")
            self.memory.add_evidence_ref(f"rejected_hyp:{hr.title}")

        # Dump models to dictionaries for the strategy engine
        val_hyps_dicts = [h.model_dump() for h in summary.validated_hypotheses]
        rej_hyps_dicts = [h.model_dump() for h in summary.rejected_hypotheses]
        root_causes_dicts = [rc.model_dump() for rc in summary.root_causes]

        # 4. Run strategy recommendations engine
        strategy_summary: StrategySummary = evaluate_strategy_recommendations(
            val_hyps_dicts, rej_hyps_dicts, root_causes_dicts
        )

        # 5. Log strategy items into memory
        self.memory.add_reasoning_step("Initiated strategy recommendation synthesis and ROI validation.")
        for o in strategy_summary.opportunities:
            self.memory.add_finding(f"Identified Opportunity: {o.title} (ROI: {o.estimated_roi:.1f}%)")
            self.memory.add_evidence_ref(f"opportunity_ref:{o.title}")

        for r in strategy_summary.recommendations:
            self.memory.add_finding(f"Proposed Recommendation: {r.title} (Priority: {r.priority})")

        for w in strategy_summary.warnings:
            self.memory.add_finding(f"Strategy Warning: {w}")

        avg_score = sum(h.confidence for h in summary.validated_hypotheses) / max(len(summary.validated_hypotheses), 1)
        self.memory.add_execution_record("average_hypothesis_confidence", avg_score)

        # 6. Aggregate findings dictionary
        return {
            "root_causes": [rc.model_dump() for rc in summary.root_causes],
            "generated_hypotheses": [h.model_dump() for h in summary.generated_hypotheses],
            "validated_hypotheses": [h.model_dump() for h in summary.validated_hypotheses],
            "rejected_hypotheses": [h.model_dump() for h in summary.rejected_hypotheses],
            "business_reasoning": summary.business_reasoning + strategy_summary.warnings,
            "business_opportunities": [o.model_dump() for o in strategy_summary.opportunities],
            "strategic_recommendations": [r.model_dump() for r in strategy_summary.recommendations],
            "risks": [rk.model_dump() for rk in strategy_summary.risks],
            "implementation_priorities": list(dict.fromkeys([r.title for r in strategy_summary.recommendations])),
        }

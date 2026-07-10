"""
Insight Forge V2 — AI Executive Report Generator Agent.

Aggregates findings, recommendations, and calculations from prior pipeline stages into consolidated C-suite reports.
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
from app.ai.schemas.executive import ExecutiveReport
from app.ai.utils.helpers import map_score_to_categorical_level
from app.ai.utils.executive import build_executive_report


class AIExecutiveReportGenerator(BaseAIAgent):
    """AI Executive Report Generator agent.

    Aggregates anomalies, strategic insights, and ROI calculations into concise C-suite report summary dashboards.
    """

    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        """Initialize the AI Executive Report Generator agent.

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
        """Register the system identity and report compiling templates."""
        # 1. Identity Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="ExecutiveIdentity",
                version="1.0.0",
                template_str=(
                    "You are the AI Executive Report Generator for InsightForge. Your job is to convert "
                    "technical and business analyst outputs into concise C-suite dashboards."
                ),
                prompt_type=PromptType.SYSTEM,
            )
        )

        # 2. User Report Generation Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="ExecutiveReportGeneration",
                version="1.0.0",
                template_str=(
                    "Review findings for dataset '{dataset_name}':\n"
                    "Anomalies: {anomalies}\n"
                    "Recommendations: {recommendations}\n\n"
                    "Generate the C-suite report summary."
                ),
                prompt_type=PromptType.USER,
                required_variables=["dataset_name", "anomalies", "recommendations"],
            )
        )

    async def validate_input(self, context: AIContext, *args: Any, **kwargs: Any) -> None:
        """Assert previous Analyst/Business Analyst outputs or dataset metadata invariants are provided."""
        meta = context.dataset_metadata or {}
        anomalies = meta.get("detected_anomalies") or context.previous_outputs.get("detected_anomalies")
        insights = meta.get("business_insights") or context.previous_outputs.get("business_insights")

        if anomalies is None or insights is None:
            raise AIValidationError("Missing previous Data Analyst findings (detected_anomalies or business_insights) in context.")

    async def validate_output(
        self, context: AIContext, response: AgentContractResponse
    ) -> None:
        """Verify the structured response matches all Executive Report API requirements."""
        if not response.success:
            raise AIValidationError(f"Executive Report Generation failed: {response.errors}")

        findings = response.findings
        required_keys = [
            "executive_summary",
            "business_health_score",
            "key_findings",
            "strategic_recommendations",
            "warnings",
        ]
        for key in required_keys:
            if key not in findings:
                raise AIValidationError(f"Output findings missing required key: '{key}'")

    async def generate_confidence(
        self, context: AIContext, findings: dict[str, Any]
    ) -> ConfidenceModel:
        """Aggregate confidence scores from executive report findings."""
        score = findings.get("business_health_score", 100.0) / 100.0
        level = map_score_to_categorical_level(score)
        return ConfidenceModel(
            confidence_score=score,
            confidence_level=level,
            explanation="Executive report confidence corresponds directly to calculated health index score.",
            uncertainty="Report accuracy relies on underlying profiling precision.",
            validation_status="VALIDATED",
        )

    async def collect_evidence(self, context: AIContext, findings: dict[str, Any]) -> list[Evidence]:
        """Convert C-suite key findings and recommendations into audit evidence records."""
        evidences = []
        for kf in findings.get("key_findings", []):
            evidences.append(
                Evidence(
                    source=f"executive_finding:{kf.get('title')}",
                    supporting_columns=[],
                    statistical_support={"confidence": kf.get("confidence")},
                    business_support=kf.get("business_impact", ""),
                    confidence=kf.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for sr in findings.get("strategic_recommendations", []):
            evidences.append(
                Evidence(
                    source=f"executive_rec:{sr.get('title')}",
                    supporting_columns=[],
                    statistical_support={"roi": sr.get("estimated_roi")},
                    business_support=f"Priority: {sr.get('priority')}, Timeline: {sr.get('timeline')}, Owner: {sr.get('owner')}",
                    confidence=1.0,
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
        """Execute executive summary compilation, ranking findings, and health index modeling."""
        meta = context.dataset_metadata or {}
        dataset_name = meta.get("dataset_name", "unknown_dataset")
        anomalies = meta.get("detected_anomalies") or context.previous_outputs.get("detected_anomalies") or []
        insights = meta.get("business_insights") or context.previous_outputs.get("business_insights") or []
        opportunities = meta.get("business_opportunities") or context.previous_outputs.get("business_opportunities") or []
        recommendations = meta.get("strategic_recommendations") or context.previous_outputs.get("strategic_recommendations") or []
        warnings = meta.get("warnings") or context.previous_outputs.get("warnings") or []

        # 1. Clear memory before run
        self.memory.clear()

        # 2. Call report engine to compile summary
        report: ExecutiveReport = build_executive_report(
            dataset_name, anomalies, insights, opportunities, recommendations, warnings
        )

        # 3. Log compiled details inside agent memory
        self.memory.add_reasoning_step("Initiated executive summary compilation and dashboard ranking.")
        self.memory.add_finding(f"Report health score calculated at {report.business_health_score:.1f}%")
        self.memory.add_evidence_ref(f"report_health:{report.business_health_score:.1f}")

        for kf in report.key_findings:
            self.memory.add_finding(f"Compiled executive finding: {kf.title}")

        for rec in report.strategic_recommendations:
            self.memory.add_finding(f"Prioritized recommendation: {rec.title} (ROI: {rec.estimated_roi:.1f}%)")

        # 4. Aggregate findings dictionary
        return {
            "executive_summary": report.executive_summary,
            "business_health_score": report.business_health_score,
            "key_findings": [kf.model_dump() for kf in report.key_findings],
            "strategic_recommendations": [rec.model_dump() for rec in report.strategic_recommendations],
            "warnings": report.warnings,
        }

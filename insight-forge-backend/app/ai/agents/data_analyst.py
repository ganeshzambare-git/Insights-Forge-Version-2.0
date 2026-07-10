"""
Insight Forge V2 — AI Data Analyst Agent.

Implements automated KPI discovery, business question framing, statistical/trend calculations,
skepticism-based validation filters, outlier detection, and business insight generation.
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
from app.ai.schemas.analyst import AnalystLLMResponse
from app.ai.schemas.statistics import StatisticalSummary
from app.ai.schemas.insights import InsightSummary
from app.ai.utils.helpers import map_score_to_categorical_level
from app.ai.utils.statistics import run_statistical_analysis
from app.ai.utils.insights import generate_insights_and_anomalies, validate_statistical_findings


class AIDataAnalyst(BaseAIAgent):
    """AI Data Analyst agent.

    Responsible for understanding business context, identifying relevant business KPIs,
    framing strategic business questions, running automated statistical calculations,
    challenging weak statistical findings, and generating business-readable insights and recommendations.
    """

    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        """Initialize the AI Data Analyst agent.

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
        """Register system identity, KPI discovery, and statistical prompts."""
        # 1. Identity Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="AnalystIdentity",
                version="1.0.0",
                template_str=(
                    "You are the AI Data Analyst for InsightForge. Your job is to understand "
                    "business context, identify meaningful KPIs, and frame strategic business questions."
                ),
                prompt_type=PromptType.SYSTEM,
            )
        )

        # 2. KPI Discovery Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="KPIDiscovery",
                version="1.0.0",
                template_str=(
                    "Analyze the following dataset context:\n"
                    "Dataset Name: {dataset_name}\n"
                    "Columns: {columns}\n"
                    "Profile: {profile}\n"
                    "Constraints: {constraints}\n"
                    "Cleaning Recommendations: {cleaning_recommendations}\n\n"
                    "Automatically discover business KPIs and generate important business questions "
                    "that are answerable using this dataset. Provide required columns, priorities, "
                    "and business reasoning."
                ),
                prompt_type=PromptType.USER,
                required_variables=[
                    "dataset_name",
                    "columns",
                    "profile",
                    "constraints",
                    "cleaning_recommendations",
                ],
            )
        )

        # 3. Statistical Analysis Prompt (Reserved)
        self.prompt_manager.register(
            PromptTemplate(
                name="StatisticalAnalysis",
                version="1.0.0",
                template_str=(
                    "Generate statistical summaries, trends, and correlations "
                    "for dataset '{dataset_name}' with columns {columns}."
                ),
                prompt_type=PromptType.USER,
                required_variables=["dataset_name", "columns"],
            )
        )

    async def validate_input(self, context: AIContext, *args: Any, **kwargs: Any) -> None:
        """Assert dataset metadata invariants are provided in the context."""
        meta = context.dataset_metadata
        if not meta:
            raise AIValidationError("Missing dataset_metadata in AIContext.")

        if "columns" not in meta or not meta["columns"]:
            raise AIValidationError("Missing or empty 'columns' list in dataset_metadata.")

        if "dataset_name" not in meta or not meta["dataset_name"]:
            raise AIValidationError("Missing 'dataset_name' in dataset_metadata.")

    async def validate_output(
        self, context: AIContext, response: AgentContractResponse
    ) -> None:
        """Verify the structured response matches all API requirements."""
        if not response.success:
            raise AIValidationError(f"Agent analysis failed: {response.errors}")

        findings = response.findings
        required_keys = [
            "discovered_kpis",
            "business_questions",
            "kpi_metadata",
            "confidence",
            "warnings",
        ]
        for key in required_keys:
            if key not in findings:
                raise AIValidationError(f"Output findings missing required key: '{key}'")

        # Extended validation for statistical outputs
        if "statistical_results" in findings:
            stat_keys = [
                "statistical_results",
                "trend_analysis",
                "correlation_results",
            ]
            for key in stat_keys:
                if key not in findings:
                    raise AIValidationError(f"Output findings missing statistical key: '{key}'")

        # Extended validation for data insights and anomaly detection outputs
        if "detected_anomalies" in findings:
            insight_keys = [
                "detected_anomalies",
                "business_insights",
                "validated_findings",
                "analyst_recommendations",
            ]
            for key in insight_keys:
                if key not in findings:
                    raise AIValidationError(f"Output findings missing insight key: '{key}'")

    async def generate_confidence(
        self, context: AIContext, findings: dict[str, Any]
    ) -> ConfidenceModel:
        """Aggregate confidence scores from findings."""
        score = findings.get("confidence", 0.8)
        level = map_score_to_categorical_level(score)
        return ConfidenceModel(
            confidence_score=score,
            confidence_level=level,
            explanation="Analyst confidence is mapped from answerability of strategic business questions.",
            uncertainty="Priority mapping is subject to specific business context variables.",
            validation_status="VALIDATED",
        )

    async def collect_evidence(self, context: AIContext, findings: dict[str, Any]) -> list[Evidence]:
        """Convert KPIs, questions, statistics, anomalies, and insights into evidence records."""
        evidences = []
        for kpi in findings.get("discovered_kpis", []):
            evidences.append(
                Evidence(
                    source=f"kpi:{kpi.get('kpi_name')}",
                    supporting_columns=kpi.get("required_columns", []),
                    statistical_support={"confidence": kpi.get("confidence")},
                    business_support=kpi.get("business_purpose", ""),
                    confidence=kpi.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for q in findings.get("business_questions", []):
            evidences.append(
                Evidence(
                    source=f"question:{q.get('question_text')}",
                    supporting_columns=q.get("required_columns", []),
                    statistical_support={"confidence": q.get("confidence")},
                    business_support=q.get("reasoning", ""),
                    confidence=q.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        # Append evidence for statistical results
        for t in findings.get("statistical_results", []):
            evidences.append(
                Evidence(
                    source=f"stat:{t.get('analysis_type')}",
                    supporting_columns=t.get("target_columns", []),
                    statistical_support={"confidence": t.get("confidence")},
                    business_support=t.get("interpretation", ""),
                    confidence=t.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for tr in findings.get("trend_analysis", []):
            evidences.append(
                Evidence(
                    source=f"trend:{tr.get('analysis_type')}",
                    supporting_columns=tr.get("target_columns", []),
                    statistical_support={"confidence": tr.get("confidence")},
                    business_support=tr.get("interpretation", ""),
                    confidence=tr.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for c in findings.get("correlation_results", []):
            evidences.append(
                Evidence(
                    source=f"correlation:{c.get('analysis_type')}",
                    supporting_columns=c.get("target_columns", []),
                    statistical_support={"confidence": c.get("confidence")},
                    business_support=c.get("interpretation", ""),
                    confidence=c.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        # Append evidence for anomalies and insights
        for a in findings.get("detected_anomalies", []):
            evidences.append(
                Evidence(
                    source=f"anomaly:{a.get('title')}",
                    supporting_columns=a.get("affected_columns", []),
                    statistical_support={"confidence": a.get("confidence")},
                    business_support=a.get("recommendation", ""),
                    confidence=a.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        for i in findings.get("business_insights", []):
            evidences.append(
                Evidence(
                    source=f"insight:{i.get('title')}",
                    supporting_columns=i.get("affected_columns", []),
                    statistical_support={"confidence": i.get("confidence")},
                    business_support=i.get("recommendation", ""),
                    confidence=i.get("confidence", 1.0),
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
        """Execute business framing, statistical math tests, and insight/anomaly detection splits."""
        meta = context.dataset_metadata
        columns = meta["columns"]
        dataset_name = meta["dataset_name"]
        sample_rows = meta.get("sample_rows", [])

        # 1. Clear memory before run
        self.memory.clear()

        # 2. Extract profile, summary, constraints, cleaning_recs
        profile = meta.get("dataset_profile") or context.previous_outputs.get("dataset_profile") or {}
        summary = meta.get("dataset_summary") or context.previous_outputs.get("dataset_summary") or {}
        constraints = meta.get("constraint_analysis") or context.previous_outputs.get("constraint_analysis") or []
        cleaning_recs = summary.get("cleaning_recommendations") or []

        # 3. Validate Data Engineer's classifications
        col_profiles = profile.get("column_profiles", {})
        inferred_types = {}
        for col in columns:
            cp = col_profiles.get(col, {})
            declared_type = cp.get("data_type", "Unknown")

            vals = [row.get(col) for row in sample_rows]
            non_nulls = [v for v in vals if v is not None and str(v).strip() != ""]

            # Mismatch check: if declared numeric, verify parsability
            if declared_type in ["integer", "float"] and non_nulls:
                numeric_parsable = True
                for v in non_nulls:
                    try:
                        float(str(v).replace("$", "").replace(",", "").strip())
                    except ValueError:
                        numeric_parsable = False
                        break
                if not numeric_parsable:
                    warning_msg = f"Data Engineer classification mismatch: '{col}' is declared '{declared_type}' but has non-numeric values."
                    self.memory.add_finding(f"Validation Warning: {warning_msg}")
                    inferred_types[col] = "string"
                    continue

            inferred_types[col] = declared_type

        # 4. Render templates
        system_prompt = self.prompt_manager.render("AnalystIdentity", "1.0.0")
        user_prompt = self.prompt_manager.render(
            "KPIDiscovery",
            "1.0.0",
            dataset_name=dataset_name,
            columns=str(columns),
            profile=str(profile),
            constraints=str(constraints),
            cleaning_recommendations=str(cleaning_recs),
        )

        # 5. Request LLM structured completion
        llm_response: AnalystLLMResponse = await self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            schema=AnalystLLMResponse,
        )

        # 6. Execute mathematical statistical engine
        stats_summary: StatisticalSummary = run_statistical_analysis(sample_rows, inferred_types)

        # 7. Execute statistical skepticism filter & reject unsupported findings
        validation_results = validate_statistical_findings(stats_summary, len(sample_rows))
        validated = validation_results["validated"]
        rejected = validation_results["rejected"]

        # Log validation outcomes in memory
        self.memory.add_reasoning_step("Executed skepticism validation on computed statistical tests.")
        for r in rejected:
            self.memory.add_finding(f"Rejected finding: {r}")
            self.memory.add_evidence_ref(f"rejected_finding:{r}")

        # 8. Execute mathematical insight & anomaly engine
        insights_summary: InsightSummary = generate_insights_and_anomalies(
            sample_rows, inferred_types, stats_summary, cleaning_recs
        )

        # 9. Populate discovered KPIs and questions into memory
        for kpi in llm_response.discovered_kpis:
            self.memory.add_finding(f"Discovered KPI: {kpi.kpi_name}")
            self.memory.add_reasoning_step(
                f"Mapped KPI '{kpi.kpi_name}' using columns {kpi.required_columns}"
            )
            for col in kpi.required_columns:
                self.memory.add_evidence_ref(f"kpi:{kpi.kpi_name}:column:{col}")

        for q in llm_response.business_questions:
            self.memory.add_finding(f"Generated business question: {q.question_text}")
            self.memory.add_reasoning_step(
                f"Question priority: {q.priority} - Reasoning: {q.reasoning}"
            )

        # 10. Record statistical calculations, anomalies, and insights in memory
        self.memory.add_reasoning_step("Executed automated statistical engine.")
        for t in validated["tests"]:
            self.memory.add_finding(f"Discovered significant relation: {t.analysis_type} on {t.target_columns}")
            self.memory.add_evidence_ref(f"stat:{t.analysis_type}:{','.join(t.target_columns)}")

        for tr in validated["trends"]:
            self.memory.add_finding(f"Detected trend: {tr.analysis_type} on {tr.target_columns}")

        for c in validated["correlations"]:
            self.memory.add_finding(f"Discovered correlation: {c.correlation_coefficient:.4f} between {c.target_columns}")

        self.memory.add_reasoning_step("Executed anomaly and insight extraction.")
        for a in insights_summary.anomalies:
            self.memory.add_finding(f"Detected anomaly: {a.title} ({a.severity})")
            self.memory.add_evidence_ref(f"anomaly_log_evidence:{a.title}")

        for i in insights_summary.insights:
            self.memory.add_finding(f"Generated business insight: {i.title}")

        self.memory.add_execution_record("overall_confidence", llm_response.overall_confidence)

        # 11. Format response evidence structures
        analyst_evidence = []
        for k in llm_response.discovered_kpis:
            analyst_evidence.append({
                "source": f"kpi:{k.kpi_name}",
                "supporting_columns": k.required_columns,
                "confidence": k.confidence,
                "business_support": k.business_purpose
            })
        for q in llm_response.business_questions:
            analyst_evidence.append({
                "source": f"question:{q.question_text}",
                "supporting_columns": q.required_columns,
                "confidence": q.confidence,
                "business_support": q.reasoning
            })

        # Compile validated findings list
        val_c = [c.model_dump() for c in validated["correlations"]]
        val_tr = [tr.model_dump() for tr in validated["trends"]]
        val_t = [t.model_dump() for t in validated["tests"]]
        validated_findings_dump = val_c + val_tr + val_t

        # Compile actionable recommendations from anomalies and insights
        analyst_recs = list(set(
            [a.recommendation for a in insights_summary.anomalies] +
            [i.recommendation for i in insights_summary.insights]
        ))
        if not analyst_recs:
            analyst_recs = ["Maintain standard data pipeline validations and ingest audits."]

        # 12. Aggregate findings dictionary
        return {
            "discovered_kpis": [kpi.model_dump() for kpi in llm_response.discovered_kpis],
            "business_questions": [q.model_dump() for q in llm_response.business_questions],
            "kpi_metadata": {k.kpi_name: k.model_dump() for k in llm_response.discovered_kpis},
            "confidence": llm_response.overall_confidence,
            "warnings": llm_response.warnings + stats_summary.warnings + rejected,
            "statistical_results": [t.model_dump() for t in stats_summary.tests],
            "trend_analysis": [tr.model_dump() for tr in stats_summary.trends],
            "correlation_results": [c.model_dump() for c in stats_summary.correlations],
            "analyst_evidence": analyst_evidence,
            "detected_anomalies": [a.model_dump() for a in insights_summary.anomalies],
            "business_insights": [i.model_dump() for i in insights_summary.insights],
            "validated_findings": validated_findings_dump,
            "analyst_recommendations": analyst_recs,
        }

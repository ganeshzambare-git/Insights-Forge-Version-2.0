"""
Insight Forge V2 — AI Data Engineer Agent.

Implements dataset understanding, semantic analysis, classification logic,
professional data profiling, and intelligent data cleaning calculations.
"""

from typing import Any
from pydantic import BaseModel, Field

from app.ai.base.agent import BaseAIAgent
from app.ai.context.model import AIContext
from app.ai.contracts.agent import AgentContractResponse
from app.ai.evidence.model import Evidence
from app.ai.exceptions.custom import AIValidationError
from app.ai.llm.provider import BaseLLMProvider
from app.ai.memory.model import AgentMemory
from app.ai.prompts.manager import PromptManager, PromptTemplate, PromptType
from app.ai.schemas.confidence import ConfidenceModel
from app.ai.schemas.profiler import DatasetProfile
from app.ai.utils.cleaning import generate_trusted_dataset
from app.ai.utils.helpers import map_score_to_categorical_level
from app.ai.utils.profiler import profile_dataset


class ColumnUnderstandingItem(BaseModel):
    """Semantic analysis and classification metadata for a single column."""

    column_name: str = Field(..., description="Original column key/header.")
    business_meaning: str = Field(
        ...,
        description="Expanded human-readable business explanation (e.g. Qty -> Quantity Sold).",
    )
    classification: str = Field(
        ...,
        description=(
            "Classification category: Identifier, Measure, Dimension, Timestamp, "
            "Categorical, Boolean, Geographic, Financial, Text, or Unknown."
        ),
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Inference confidence score.")
    reasoning: str = Field(..., description="Explanation logic behind the classification.")
    evidence: str = Field(
        ...,
        description="Structural or contextual proof (e.g. presence of currency symbol, date formatting).",
    )


class DatasetUnderstandingLLMResponse(BaseModel):
    """Consolidated LLM output schema for dataset semantic analysis."""

    estimated_industry: str = Field(..., description="Target business industry (e.g. Retail, Healthcare).")
    estimated_business_domain: str = Field(
        ...,
        description="Business area context (e.g. Sales, Operations).",
    )
    estimated_business_process: str = Field(
        ...,
        description="Core workflow process (e.g. Order Processing).",
    )
    row_representation: str = Field(
        ...,
        description="Descriptive meaning representing what one single database row contains.",
    )
    detected_entities: list[str] = Field(
        default_factory=list,
        description="Major conceptual entities identified (e.g. Customer, Order, Product).",
    )
    columns: list[ColumnUnderstandingItem] = Field(
        default_factory=list,
        description="Metadata analysis mapping for every column.",
    )
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated average confidence for the dataset understanding.",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Analytical assumptions made about abbreviations or missing schemas.",
    )


class AIDataEngineer(BaseAIAgent):
    """AI Data Engineer agent.

    Responsible for initial dataset loading audits, column categorization,
    semantic parsing, professional data profiling, and intelligent data cleaning checks.
    """

    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        """Initialize the AI Data Engineer agent.

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
        """Central registration of prompts required for Phase 2, 3, and 4."""
        # 1. Identity Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="Identity",
                version="1.0.0",
                template_str=(
                    "You are the AI Data Engineer for InsightForge. Your job is to analyze "
                    "dataset schemas, columns, and sample rows to understand their structure, "
                    "domain, and semantics."
                ),
                prompt_type=PromptType.SYSTEM,
            )
        )

        # 2. Dataset Understanding Prompt
        self.prompt_manager.register(
            PromptTemplate(
                name="DatasetUnderstanding",
                version="1.0.0",
                template_str=(
                    "Analyze the following dataset metadata:\n"
                    "Dataset Name: {dataset_name}\n"
                    "Columns: {columns}\n"
                    "Sample Rows: {sample_rows}\n\n"
                    "Perform semantic understanding, abbreviation mapping, row definition, "
                    "and column classifications (Identifier, Measure, Dimension, etc.)."
                ),
                prompt_type=PromptType.USER,
                required_variables=["dataset_name", "columns", "sample_rows"],
            )
        )

        # 3. Semantic Analysis Prompt (Reserved)
        self.prompt_manager.register(
            PromptTemplate(
                name="SemanticAnalysis",
                version="1.0.0",
                template_str=(
                    "Given columns {columns}, map abbreviations (e.g. Qty, Amt, DOB) "
                    "to expanded business concepts."
                ),
                prompt_type=PromptType.USER,
                required_variables=["columns"],
            )
        )

        # 4. Column Classification Prompt (Reserved)
        self.prompt_manager.register(
            PromptTemplate(
                name="ColumnClassification",
                version="1.0.0",
                template_str=(
                    "Classify column '{column_name}' with values {samples} "
                    "into Dimension, Measure, Identifier, Geographic, etc."
                ),
                prompt_type=PromptType.USER,
                required_variables=["column_name", "samples"],
            )
        )

        # 5. Data Profiling Prompt (Reserved)
        self.prompt_manager.register(
            PromptTemplate(
                name="DataProfiling",
                version="1.0.0",
                template_str=(
                    "Perform professional data profiling on the dataset named {dataset_name} "
                    "with columns {columns} and sample rows {sample_rows}."
                ),
                prompt_type=PromptType.USER,
                required_variables=["dataset_name", "columns", "sample_rows"],
            )
        )

        # 6. Data Cleaning Prompt (Reserved)
        self.prompt_manager.register(
            PromptTemplate(
                name="DataCleaning",
                version="1.0.0",
                template_str=(
                    "Analyze data quality issues for the dataset '{dataset_name}' with columns "
                    "{columns} and sample rows {sample_rows}, recommending severity-based actions."
                ),
                prompt_type=PromptType.USER,
                required_variables=["dataset_name", "columns", "sample_rows"],
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
            "estimated_industry",
            "estimated_business_domain",
            "estimated_business_process",
            "row_representation",
            "detected_entities",
            "columns_understanding",
            "metadata",
        ]
        for key in required_keys:
            if key not in findings:
                raise AIValidationError(f"Output findings missing required key: '{key}'")

        # Extended validation for data profiling outputs if profiling was active
        if "dataset_profile" in findings:
            profiling_keys = [
                "dataset_profile",
                "column_profiles",
                "quality_metrics",
                "constraint_analysis",
                "profiling_summary",
                "warnings",
            ]
            for key in profiling_keys:
                if key not in findings:
                    raise AIValidationError(f"Output findings missing data profiling key: '{key}'")

        # Extended validation for data cleaning outputs if cleaning was active
        if "dataset_summary" in findings:
            cleaning_keys = [
                "dataset_summary",
                "cleaning_log",
                "certification_status",
            ]
            for key in cleaning_keys:
                if key not in findings:
                    raise AIValidationError(f"Output findings missing data cleaning key: '{key}'")

    async def generate_confidence(
        self, context: AIContext, findings: dict[str, Any]
    ) -> ConfidenceModel:
        """Aggregate confidence scores from metadata analysis findings."""
        score = findings.get("overall_confidence", 0.8)
        level = map_score_to_categorical_level(score)
        return ConfidenceModel(
            confidence_score=score,
            confidence_level=level,
            explanation="Overall confidence generated from the statistical mapping of column values.",
            uncertainty="Abbreviation expansions are inferred without direct user interaction.",
            validation_status="VALIDATED",
        )

    async def collect_evidence(self, context: AIContext, findings: dict[str, Any]) -> list[Evidence]:
        """Convert column classification, constraint, and cleaning details into evidence."""
        evidences = []
        for col_name, details in findings.get("columns_understanding", {}).items():
            evidences.append(
                Evidence(
                    source=f"column:{col_name}",
                    supporting_columns=[col_name],
                    statistical_support={"confidence": details.get("confidence")},
                    business_support=details.get("reasoning", ""),
                    confidence=details.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        # Append evidence for constraints if present
        for c in findings.get("constraint_analysis", []):
            evidences.append(
                Evidence(
                    source=f"constraint:{c.get('constraint_type')}",
                    supporting_columns=c.get("columns", []),
                    statistical_support={"confidence": c.get("confidence")},
                    business_support=c.get("reasoning", ""),
                    confidence=c.get("confidence", 1.0),
                    validation_status="CONFIRMED",
                )
            )

        # Append evidence for cleaning recommendations
        summary = findings.get("dataset_summary", {})
        for r in summary.get("cleaning_recommendations", []):
            evidences.append(
                Evidence(
                    source=f"cleaning:{r.get('issue_type')}",
                    supporting_columns=r.get("affected_columns", []),
                    statistical_support={"confidence": r.get("confidence")},
                    business_support=r.get("reasoning", ""),
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
        """Execute understanding, profiling, and cleaning logic, mapping outputs and memory logs."""
        meta = context.dataset_metadata
        columns = meta["columns"]
        sample_rows = meta.get("sample_rows", [])
        dataset_name = meta["dataset_name"]
        row_count = meta.get("row_count") or len(sample_rows)

        # 1. Clear memory before run
        self.memory.clear()

        # 2. Render templates
        system_prompt = self.prompt_manager.render("Identity", "1.0.0")
        user_prompt = self.prompt_manager.render(
            "DatasetUnderstanding",
            "1.0.0",
            dataset_name=dataset_name,
            columns=str(columns),
            sample_rows=str(sample_rows),
        )

        # 3. Request LLM structured completion
        llm_response: DatasetUnderstandingLLMResponse = await self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            schema=DatasetUnderstandingLLMResponse,
        )

        # 4. Execute data profiling if sample rows are available
        profile: DatasetProfile = profile_dataset(sample_rows, columns, dataset_name)

        # 5. Execute data cleaning checks
        clean_summary, clean_log = generate_trusted_dataset(sample_rows, columns, dataset_name)

        # Synchronize quality score to use the centralized deduplicated score
        profile.overall_quality_score = clean_summary.overall_quality_score

        # 6. Process and categorize columns for metadata
        columns_understanding = {}
        detected_measures = []
        detected_dimensions = []
        detected_identifiers = []
        detected_timestamp_columns = []

        for col in llm_response.columns:
            columns_understanding[col.column_name] = {
                "business_meaning": col.business_meaning,
                "classification": col.classification,
                "confidence": col.confidence,
                "reasoning": col.reasoning,
                "evidence": col.evidence,
            }

            # Map categories to metadata types
            cls_lower = col.classification.lower()
            if cls_lower in ["measure", "financial"]:
                detected_measures.append(col.column_name)
            elif cls_lower in ["dimension", "categorical", "geographic", "text"]:
                detected_dimensions.append(col.column_name)
            elif cls_lower == "identifier":
                detected_identifiers.append(col.column_name)
            elif cls_lower == "timestamp":
                detected_timestamp_columns.append(col.column_name)

            # Record semantic decisions and classifications in memory
            self.memory.add_reasoning_step(
                f"Mapped '{col.column_name}' to business concept '{col.business_meaning}'"
            )
            self.memory.add_reasoning_step(
                f"Classified '{col.column_name}' as a '{col.classification}'"
            )

        # 7. Populate entities and assumptions in memory
        for entity in llm_response.detected_entities:
            self.memory.add_finding(f"Detected business entity: {entity}")

        for assumption in llm_response.assumptions:
            self.memory.add_hypothesis(f"Assumption: {assumption}", accepted=True)

        self.memory.add_execution_record("overall_confidence", llm_response.overall_confidence)

        # 8. Record profiling actions in memory
        self.memory.add_reasoning_step("Executed professional data profiling.")
        self.memory.add_finding(f"Dataset Quality Score: {profile.overall_quality_score}")
        for c in profile.constraints:
            self.memory.add_finding(f"Discovered constraint: {c.constraint_type} on {c.columns}")
            self.memory.add_evidence_ref(f"constraint:{c.constraint_type}:{','.join(c.columns)}")
        self.memory.add_execution_record("profiling_quality_score", profile.overall_quality_score)

        # 9. Record cleaning decisions, quality metrics, and certification in memory
        self.memory.add_reasoning_step("Executed intelligent data cleaning analysis.")
        self.memory.add_finding(f"Cleaning overall score: {clean_summary.overall_quality_score}")
        self.memory.add_finding(f"Dataset certified status: {clean_summary.certification_status}")
        
        for entry in clean_log:
            # Storing cleaning decisions/proposals
            self.memory.add_finding(f"Proposed cleaning action: {entry.recommendation} for {entry.issue}")
            # Logging evidence references
            self.memory.add_evidence_ref(f"cleaning_log_evidence:{entry.issue}")
            
        self.memory.add_execution_record("certification_history", clean_summary.certification_status)

        # 10. Build response metadata structure
        findings_metadata = {
            "dataset_name": dataset_name,
            "row_count": row_count,
            "column_count": len(columns),
            "estimated_industry": llm_response.estimated_industry,
            "estimated_business_domain": llm_response.estimated_business_domain,
            "detected_entities": llm_response.detected_entities,
            "detected_measures": detected_measures,
            "detected_dimensions": detected_dimensions,
            "detected_identifiers": detected_identifiers,
            "detected_timestamp_columns": detected_timestamp_columns,
            "overall_confidence": llm_response.overall_confidence,
        }

        # 11. Aggregate findings dictionary
        return {
            "estimated_industry": llm_response.estimated_industry,
            "estimated_business_domain": llm_response.estimated_business_domain,
            "estimated_business_process": llm_response.estimated_business_process,
            "row_representation": llm_response.row_representation,
            "detected_entities": llm_response.detected_entities,
            "columns_understanding": columns_understanding,
            "overall_confidence": llm_response.overall_confidence,
            "metadata": findings_metadata,
            "dataset_profile": profile.model_dump(),
            "column_profiles": {col: p.model_dump() for col, p in profile.column_profiles.items()},
            "quality_metrics": {
                "overall_quality_score": profile.overall_quality_score,
            },
            "constraint_analysis": [c.model_dump() for c in profile.constraints],
            "profiling_summary": (
                f"Dataset contains {row_count} rows and {len(columns)} columns. "
                f"Overall quality score is {profile.overall_quality_score:.2f}."
            ),
            "warnings": profile.warnings,
            "dataset_summary": clean_summary.model_dump(),
            "cleaning_log": [e.model_dump() for e in clean_log],
            "certification_status": clean_summary.certification_status,
        }

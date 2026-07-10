"""
Insight Forge V2 — AI Service layer.

Coordinates uploaded file parsing, context compilation, and execution of the multi-agent pipeline orchestrator.
"""

import csv
import json
import io
from typing import Any
import uuid

from app.services.context import ServiceContext
from app.services.audit import DefaultAuditLogger
from app.services.providers import SystemClockProvider, SystemUUIDProvider
from app.services.uow import UnitOfWork

from app.ai import (
    AIContext,
    AIDataEngineer,
    AIDataAnalyst,
    AIBusinessAnalyst,
    AIExecutiveReportGenerator,
    AIWorkflowOrchestrator,
    OrchestratedPipelineResult,
)
from app.ai.llm.provider import BaseLLMProvider
from app.ai.agents.data_engineer import DatasetUnderstandingLLMResponse, ColumnUnderstandingItem
from app.ai.schemas.analyst import AnalystLLMResponse, KPIMetadata, BusinessQuestion
from pydantic import BaseModel


class DefaultLLMProvider(BaseLLMProvider):
    """Fallback LLM provider returning mock structures for pipeline coordination."""

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
                estimated_industry="Education",
                estimated_business_domain="Student Management",
                estimated_business_process="Academic Performance Auditing",
                row_representation="A single student's course grading record.",
                detected_entities=["Student", "Course", "Instructor"],
                columns=[
                    ColumnUnderstandingItem(
                        column_name="student_id",
                        business_meaning="Unique student registration ID",
                        classification="Identifier",
                        confidence=0.98,
                        reasoning="Numeric ID format",
                        evidence="Header ends with id",
                    ),
                    ColumnUnderstandingItem(
                        column_name="grade",
                        business_meaning="Course Grade Percentage Score",
                        classification="Measure",
                        confidence=0.95,
                        reasoning="Numeric percentage value",
                        evidence="Contains numbers from 0-100",
                    )
                ],
                overall_confidence=0.95,
                assumptions=["Grade is on 0-100 scale"],
            )
        elif schema is AnalystLLMResponse:
            return AnalystLLMResponse(
                discovered_kpis=[
                    KPIMetadata(
                        kpi_name="Average Grade",
                        description="Mean of grades column",
                        required_columns=["grade"],
                        aggregation_type="AVERAGE",
                        business_purpose="Audit general academic performance",
                        confidence=0.90,
                    )
                ],
                business_questions=[
                    BusinessQuestion(
                        question_text="What is the average student grade?",
                        priority="High",
                        confidence=0.90,
                        required_columns=["grade"],
                        reasoning="Identify low-performing cohorts.",
                    )
                ],
                overall_confidence=0.95,
                warnings=[],
            )
        return "Mock response"

    async def generate_chat(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> Any:
        return "Mock chat response"


def parse_dataset_content(content: bytes, filename: str) -> list[dict[str, Any]]:
    """Parse CSV or JSON byte content into list of dictionaries."""
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    if filename.endswith(".json"):
        data = json.loads(decoded)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "rows" in data:
            return data["rows"]
        else:
            return [data]
    else:
        # Default to CSV parsing
        f = io.StringIO(decoded)
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


class AIService:
    """Service class executing the sequential AI multi-agent workflow."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: DefaultAuditLogger,
        clock: SystemClockProvider,
        uuid_provider: SystemUUIDProvider,
    ) -> None:
        """Initialize the AI service."""
        self.uow = uow
        self.context = context
        self.audit_logger = audit_logger
        self.clock = clock
        self.uuid = uuid_provider
        self.orchestrator = AIWorkflowOrchestrator()
        self.llm_provider = DefaultLLMProvider()

    async def run_ai_analysis(
        self,
        tenant_id: uuid.UUID,
        file_content: bytes,
        filename: str,
        options: dict[str, Any] | None = None,
    ) -> OrchestratedPipelineResult:
        """Parse the input file dataset and trigger the sequential orchestrated workflow pipeline."""
        # 1. Parse dataset file contents
        sample_rows = parse_dataset_content(file_content, filename)
        if not sample_rows:
            return OrchestratedPipelineResult(
                success=False,
                metrics=[],
                consolidated_report={},
                warnings=["Empty dataset uploaded. Analysis aborted."],
            )

        # 2. Extract column headers list
        columns = list(sample_rows[0].keys())

        # 3. Create context model
        ai_context = AIContext(
            tenant_id=str(tenant_id),
            dataset_metadata={
                "dataset_name": filename.split(".")[0],
                "columns": columns,
                "sample_rows": sample_rows,
                "row_count": len(sample_rows),
            },
        )

        # 4. Instantiate agents
        engineer = AIDataEngineer(name="data-engineer", llm_provider=self.llm_provider)
        analyst = AIDataAnalyst(name="data-analyst", llm_provider=self.llm_provider)
        business = AIBusinessAnalyst(name="business-analyst", llm_provider=self.llm_provider)
        executive = AIExecutiveReportGenerator(name="executive-report", llm_provider=self.llm_provider)

        # 5. Run the orchestrator
        return await self.orchestrator.run_pipeline(
            ai_context, engineer, analyst, business, executive
        )

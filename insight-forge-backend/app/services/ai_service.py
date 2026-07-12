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

from app.ai import OrchestratedPipelineResult
from app.ai.orchestration.runner import run_pipeline_on_rows


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

        # 2. Run the shared deterministic pipeline over the parsed rows.
        columns = list(sample_rows[0].keys())
        return await run_pipeline_on_rows(
            tenant_id=tenant_id,
            dataset_name=filename.rsplit(".", 1)[0],
            columns=columns,
            sample_rows=sample_rows,
        )

"""
Insight Forge V2 — Pipeline Runner.

Single reusable entry point that assembles the deterministic inference provider,
the four agents, and the orchestrator, then runs the multi-agent pipeline over a
set of parsed rows. Shared by the live upload endpoint and the stored-dataset
report endpoint so both execute identical, real (non-mock) analysis.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.ai.context.model import AIContext
from app.ai.agents.data_engineer import AIDataEngineer
from app.ai.agents.data_analyst import AIDataAnalyst
from app.ai.agents.business_analyst import AIBusinessAnalyst
from app.ai.agents.executive_report import AIExecutiveReportGenerator
from app.ai.orchestration.orchestrator import AIWorkflowOrchestrator
from app.ai.orchestration.pipeline import OrchestratedPipelineResult
from app.ai.llm.heuristic_provider import HeuristicInferenceProvider


async def run_pipeline_on_rows(
    tenant_id: uuid.UUID,
    dataset_name: str,
    columns: list[str],
    sample_rows: list[dict[str, Any]],
) -> OrchestratedPipelineResult:
    """Run the full deterministic multi-agent pipeline over already-parsed rows.

    Args:
        tenant_id: Owning tenant UUID (for context/isolation traceability).
        dataset_name: Human-readable dataset label.
        columns: Ordered list of column headers.
        sample_rows: Parsed dataset rows as dictionaries.

    Returns:
        The consolidated orchestrated pipeline result.
    """
    if not sample_rows:
        return OrchestratedPipelineResult(
            success=False,
            metrics=[],
            consolidated_report={},
            warnings=["Empty dataset provided. Analysis aborted."],
        )

    context = AIContext(
        tenant_id=str(tenant_id),
        dataset_metadata={
            "dataset_name": dataset_name,
            "columns": columns,
            "sample_rows": sample_rows,
            "row_count": len(sample_rows),
        },
    )

    provider = HeuristicInferenceProvider(
        dataset_name=dataset_name, columns=columns, sample_rows=sample_rows
    )
    engineer = AIDataEngineer(name="data-engineer", llm_provider=provider)
    analyst = AIDataAnalyst(name="data-analyst", llm_provider=provider)
    business = AIBusinessAnalyst(name="business-analyst", llm_provider=provider)
    executive = AIExecutiveReportGenerator(name="executive-report", llm_provider=provider)

    orchestrator = AIWorkflowOrchestrator()
    return await orchestrator.run_pipeline(context, engineer, analyst, business, executive)

"""
Insight Forge V2 — Multi-Agent Pipeline Orchestrator.

Sequentially triggers Data Engineer, Data Analyst, Business Analyst, and Executive Report Generator
agents, carrying findings down the pipeline and tracking execution performance metrics.
"""

import time

from app.ai.context.model import AIContext
from app.ai.agents.data_engineer import AIDataEngineer
from app.ai.agents.data_analyst import AIDataAnalyst
from app.ai.agents.business_analyst import AIBusinessAnalyst
from app.ai.agents.executive_report import AIExecutiveReportGenerator
from app.ai.orchestration.pipeline import AgentStepMetric, OrchestratedPipelineResult


class AIWorkflowOrchestrator:
    """Workflow controller sequentially executing the InsightForge multi-agent pipeline layers."""

    async def run_pipeline(
        self,
        context: AIContext,
        data_engineer: AIDataEngineer,
        data_analyst: AIDataAnalyst,
        business_analyst: AIBusinessAnalyst,
        executive_report: AIExecutiveReportGenerator,
    ) -> OrchestratedPipelineResult:
        """Execute the multi-agent pipeline sequentially, updating state and timing metrics.

        Hhalts execution immediately and returns failure diagnostics if any step fails.
        """
        metrics = []
        warnings = []
        consolidated = {}

        # 1. AI Data Engineer
        start_time = time.perf_counter()
        try:
            eng_res = await data_engineer.execute(context)
            duration = (time.perf_counter() - start_time) * 1000.0
            if not eng_res.success:
                metrics.append(
                    AgentStepMetric(
                        agent_name=data_engineer.name,
                        execution_time_ms=duration,
                        status="Failure",
                        error=str(eng_res.errors),
                    )
                )
                return OrchestratedPipelineResult(
                    success=False,
                    metrics=metrics,
                    consolidated_report=consolidated,
                    warnings=warnings,
                )

            metrics.append(
                AgentStepMetric(
                    agent_name=data_engineer.name,
                    execution_time_ms=duration,
                    status="Success",
                )
            )
            # Propagate engineer outputs to context state and consolidated report dict
            context.previous_outputs.update(eng_res.findings)
            context.dataset_metadata.update(eng_res.findings)
            consolidated.update(eng_res.findings)
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000.0
            metrics.append(
                AgentStepMetric(
                    agent_name=data_engineer.name,
                    execution_time_ms=duration,
                    status="Failure",
                    error=str(e),
                )
            )
            return OrchestratedPipelineResult(
                success=False,
                metrics=metrics,
                consolidated_report=consolidated,
                warnings=warnings,
            )

        # 2. AI Data Analyst
        start_time = time.perf_counter()
        try:
            ana_res = await data_analyst.execute(context)
            duration = (time.perf_counter() - start_time) * 1000.0
            if not ana_res.success:
                metrics.append(
                    AgentStepMetric(
                        agent_name=data_analyst.name,
                        execution_time_ms=duration,
                        status="Failure",
                        error=str(ana_res.errors),
                    )
                )
                return OrchestratedPipelineResult(
                    success=False,
                    metrics=metrics,
                    consolidated_report=consolidated,
                    warnings=warnings,
                )

            metrics.append(
                AgentStepMetric(
                    agent_name=data_analyst.name,
                    execution_time_ms=duration,
                    status="Success",
                )
            )
            context.previous_outputs.update(ana_res.findings)
            context.dataset_metadata.update(ana_res.findings)
            consolidated.update(ana_res.findings)
            if "warnings" in ana_res.findings:
                warnings.extend(ana_res.findings["warnings"])
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000.0
            metrics.append(
                AgentStepMetric(
                    agent_name=data_analyst.name,
                    execution_time_ms=duration,
                    status="Failure",
                    error=str(e),
                )
            )
            return OrchestratedPipelineResult(
                success=False,
                metrics=metrics,
                consolidated_report=consolidated,
                warnings=warnings,
            )

        # 3. AI Business Analyst
        start_time = time.perf_counter()
        try:
            bus_res = await business_analyst.execute(context)
            duration = (time.perf_counter() - start_time) * 1000.0
            if not bus_res.success:
                metrics.append(
                    AgentStepMetric(
                        agent_name=business_analyst.name,
                        execution_time_ms=duration,
                        status="Failure",
                        error=str(bus_res.errors),
                    )
                )
                return OrchestratedPipelineResult(
                    success=False,
                    metrics=metrics,
                    consolidated_report=consolidated,
                    warnings=warnings,
                )

            metrics.append(
                AgentStepMetric(
                    agent_name=business_analyst.name,
                    execution_time_ms=duration,
                    status="Success",
                )
            )
            context.previous_outputs.update(bus_res.findings)
            context.dataset_metadata.update(bus_res.findings)
            consolidated.update(bus_res.findings)
            if "warnings" in bus_res.findings:
                warnings.extend(bus_res.findings["warnings"])
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000.0
            metrics.append(
                AgentStepMetric(
                    agent_name=business_analyst.name,
                    execution_time_ms=duration,
                    status="Failure",
                    error=str(e),
                )
            )
            return OrchestratedPipelineResult(
                success=False,
                metrics=metrics,
                consolidated_report=consolidated,
                warnings=warnings,
            )

        # 4. AI Executive Report Generator
        start_time = time.perf_counter()
        try:
            exec_res = await executive_report.execute(context)
            duration = (time.perf_counter() - start_time) * 1000.0
            if not exec_res.success:
                metrics.append(
                    AgentStepMetric(
                        agent_name=executive_report.name,
                        execution_time_ms=duration,
                        status="Failure",
                        error=str(exec_res.errors),
                    )
                )
                return OrchestratedPipelineResult(
                    success=False,
                    metrics=metrics,
                    consolidated_report=consolidated,
                    warnings=warnings,
                )

            metrics.append(
                AgentStepMetric(
                    agent_name=executive_report.name,
                    execution_time_ms=duration,
                    status="Success",
                )
            )
            context.previous_outputs.update(exec_res.findings)
            context.dataset_metadata.update(exec_res.findings)
            consolidated.update(exec_res.findings)
            if "warnings" in exec_res.findings:
                warnings.extend(exec_res.findings["warnings"])
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000.0
            metrics.append(
                AgentStepMetric(
                    agent_name=executive_report.name,
                    execution_time_ms=duration,
                    status="Failure",
                    error=str(e),
                )
            )
            return OrchestratedPipelineResult(
                success=False,
                metrics=metrics,
                consolidated_report=consolidated,
                warnings=warnings,
            )

        # Deduplicate warnings while preserving order
        unique_warnings = []
        for w in warnings:
            if w not in unique_warnings:
                unique_warnings.append(w)

        return OrchestratedPipelineResult(
            success=True,
            metrics=metrics,
            consolidated_report=consolidated,
            warnings=unique_warnings,
        )

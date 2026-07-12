"""
Insight Forge V2 — Dataset Service.

Handles ingestion of arbitrary tabular uploads into generic per-tenant storage,
dataset listing/retrieval, and running the deterministic analysis pipeline over
stored rows. No external services or mock data are used.
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Sequence

from app.ai.orchestration.pipeline import OrchestratedPipelineResult
from app.ai.orchestration.runner import run_pipeline_on_rows
from app.ai.utils.profiler import profile_dataset
from app.models.dataset import Dataset, DatasetRecord
from app.repositories.dataset import DatasetRepository, DatasetRecordRepository
from app.repositories.tenant import TenantRepository
from app.services.audit import AuditLoggerProtocol
from app.services.base import BaseService
from app.services.context import ServiceContext
from app.services.exceptions import NotFoundError, ValidationError
from app.services.ai_service import parse_dataset_content
from app.services.providers import ClockProvider, UUIDProvider
from app.services.result import ServiceResult
from app.services.uow import UnitOfWork

# Cap stored rows per upload to keep a single request bounded.
MAX_INGEST_ROWS = 50_000


@dataclass(frozen=True)
class IngestionOutcome:
    """Result of an ingestion: the persisted dataset plus its detected columns."""

    dataset: "Dataset"
    columns: list[str]


class DatasetService(BaseService):
    """Business service governing dataset ingestion and retrieval."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = DatasetRepository(session=uow.session)
        self.record_repo = DatasetRecordRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)

    async def ingest(
        self, tenant_id: uuid.UUID, filename: str, content: bytes
    ) -> ServiceResult[IngestionOutcome]:
        """Parse an uploaded file and persist it as a dataset plus its rows.

        Args:
            tenant_id: Owning tenant UUID.
            filename: Original uploaded filename.
            content: Raw file bytes (CSV or JSON).

        Returns:
            A ServiceResult wrapping the persisted dataset and its columns.
        """
        rows = parse_dataset_content(content, filename)
        if not rows:
            raise ValidationError(
                "Uploaded file contains no parseable rows.",
                error_code="empty_dataset",
            )
        if len(rows) > MAX_INGEST_ROWS:
            raise ValidationError(
                f"Dataset exceeds the maximum of {MAX_INGEST_ROWS} rows per upload.",
                error_code="dataset_too_large",
            )

        columns = list(rows[0].keys())
        source_format = "json" if filename.lower().endswith(".json") else "csv"
        dataset_name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # Deterministic data-quality score (0-100) from the profiler.
        profile = profile_dataset(rows, columns, dataset_name)
        health_score = Decimal(str(round(profile.overall_quality_score * 100, 2)))

        async def action() -> IngestionOutcome:
            if not await self.tenant_repo.exists(tenant_id=tenant_id):
                raise NotFoundError(
                    f"Tenant '{tenant_id}' does not exist.",
                    error_code="tenant_not_found",
                )

            dataset = Dataset(
                dataset_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                original_filename=filename,
                source_format=source_format,
                processing_status="Ready",
                row_count=len(rows),
                size_bytes=len(content),
                health_score=health_score,
            )
            await self.repo.create(dataset)

            records = [
                DatasetRecord(
                    dataset_id=dataset.dataset_id,
                    tenant_id=tenant_id,
                    row_index=index,
                    payload=row,
                )
                for index, row in enumerate(rows)
            ]
            await self.record_repo.bulk_add(records)
            return IngestionOutcome(dataset=dataset, columns=columns)

        return await self.execute_command(
            "ingest",
            action,
            success_msg=f"Dataset '{dataset_name}' ingested with {len(rows)} rows.",
        )

    async def list_datasets(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[Dataset]:
        """List datasets for a tenant, newest first."""
        return await self.repo.list_by_tenant(tenant_id, limit=limit, offset=offset)

    async def get_dataset(
        self, tenant_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> Dataset:
        """Fetch a single dataset, enforcing tenant ownership."""
        dataset = await self.repo.get_by_id(dataset_id)
        if not dataset or dataset.tenant_id != tenant_id:
            raise NotFoundError(
                f"Dataset '{dataset_id}' not found.", error_code="dataset_not_found"
            )
        return dataset

    async def get_records(
        self,
        tenant_id: uuid.UUID,
        dataset_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[DatasetRecord]:
        """Return stored rows for a dataset (tenant-checked)."""
        await self.get_dataset(tenant_id, dataset_id)
        return await self.record_repo.list_by_dataset(dataset_id, limit=limit, offset=offset)

    async def build_report(
        self, tenant_id: uuid.UUID, dataset_id: uuid.UUID
    ) -> OrchestratedPipelineResult:
        """Run the deterministic multi-agent pipeline over a stored dataset."""
        dataset = await self.get_dataset(tenant_id, dataset_id)
        rows: list[dict[str, Any]] = await self.record_repo.all_payloads(dataset_id)
        columns = list(rows[0].keys()) if rows else []
        return await run_pipeline_on_rows(
            tenant_id=tenant_id,
            dataset_name=dataset.dataset_name,
            columns=columns,
            sample_rows=rows,
        )

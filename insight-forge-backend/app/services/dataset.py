"""
Insight Forge V2 — Dataset Service.

Orchestrates dataset registration, lookup, listing, and status transitions.
The backend only tracks dataset metadata and lifecycle — it never parses or
cleans the underlying file (that belongs to the cleaning worker).
"""

import uuid
from decimal import Decimal
from typing import Sequence

from app.core.enums import DatasetStatus
from app.models.dataset import Dataset
from app.repositories.dataset import DatasetRepository
from app.repositories.tenant import TenantRepository
from app.services.audit import AuditLoggerProtocol
from app.services.base import BaseService
from app.services.context import ServiceContext
from app.services.exceptions import NotFoundError, ValidationError
from app.services.providers import ClockProvider, UUIDProvider
from app.services.result import ServiceResult
from app.services.uow import UnitOfWork


class DatasetService(BaseService):
    """Business service governing the Dataset lifecycle."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the DatasetService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = DatasetRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)

    async def register_dataset(
        self,
        tenant_id: uuid.UUID,
        original_filename: str,
        source_format: str,
        size_bytes: int | None = None,
    ) -> ServiceResult[Dataset]:
        """Register a new dataset record in the ``Pending`` state.

        Args:
            tenant_id: Owning tenant UUID.
            original_filename: Original uploaded filename.
            source_format: File format / source type.
            size_bytes: Optional file size in bytes.

        Returns:
            A ServiceResult wrapping the created Dataset entity.
        """
        filename = original_filename.strip()
        fmt = source_format.strip().lower()

        async def action() -> Dataset:
            await self._validate_register_request(tenant_id, filename, fmt)

            dataset = Dataset(
                dataset_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                original_filename=filename,
                source_format=fmt,
                processing_status=DatasetStatus.PENDING.value,
                size_bytes=size_bytes,
            )
            created = await self.repo.create(dataset)
            self.publish_domain_event(
                "DatasetRegistered",
                {
                    "dataset_id": str(created.dataset_id),
                    "tenant_id": str(tenant_id),
                },
            )
            return created

        return await self.execute_command(
            "register_dataset",
            action,
            success_msg=f"Dataset '{filename}' registered successfully.",
        )

    async def get_dataset(self, dataset_id: uuid.UUID) -> Dataset | None:
        """Fetch a single Dataset by ID.

        Args:
            dataset_id: Dataset UUID.

        Returns:
            The Dataset entity if found, otherwise None.
        """
        return await self.repo.get_by_id(dataset_id)

    async def list_datasets(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[Dataset]:
        """List datasets belonging to a specific tenant (tenant-scoped).

        Args:
            tenant_id: Owning tenant UUID.
            limit: Maximum number of records to return.
            offset: Offset skip count.

        Returns:
            A sequence of Dataset entities, newest first.
        """
        return await self.repo.get_by_tenant(
            tenant_id=tenant_id, limit=limit, offset=offset
        )

    async def update_status(
        self,
        dataset_id: uuid.UUID,
        processing_status: DatasetStatus | None = None,
        health_score: Decimal | None = None,
        row_count: int | None = None,
    ) -> ServiceResult[Dataset]:
        """Update a dataset's processing status and/or health metrics.

        Args:
            dataset_id: Target Dataset UUID.
            processing_status: New processing status, if changing.
            health_score: Data-quality score (0-100), if computed.
            row_count: Cleaned row count, if computed.

        Returns:
            A ServiceResult wrapping the updated Dataset entity.
        """

        async def action() -> Dataset:
            dataset = await self.repo.get_by_id(dataset_id)
            if not dataset:
                raise NotFoundError(
                    f"Dataset with ID '{dataset_id}' not found.",
                    error_code="dataset_not_found",
                )

            updates: dict[str, object] = {}
            if processing_status is not None:
                updates["processing_status"] = processing_status.value
            if health_score is not None:
                updates["health_score"] = health_score
            if row_count is not None:
                updates["row_count"] = row_count

            if not updates:
                raise ValidationError(
                    "No updatable fields supplied.",
                    error_code="no_update_fields",
                )

            return await self.repo.update(dataset, **updates)

        return await self.execute_command(
            "update_dataset_status",
            action,
            success_msg=f"Dataset '{dataset_id}' updated successfully.",
        )

    async def delete_dataset(self, dataset_id: uuid.UUID) -> ServiceResult[None]:
        """Delete a dataset record.

        Args:
            dataset_id: Target Dataset UUID.

        Returns:
            A ServiceResult indicating deletion status.
        """

        async def action() -> None:
            dataset = await self.repo.get_by_id(dataset_id)
            if not dataset:
                raise NotFoundError(
                    f"Dataset with ID '{dataset_id}' not found.",
                    error_code="dataset_not_found",
                )
            await self.repo.delete(dataset)

        return await self.execute_command(
            "delete_dataset",
            action,
            success_msg=f"Dataset '{dataset_id}' deleted successfully.",
        )

    # Private Helpers
    async def _validate_register_request(
        self, tenant_id: uuid.UUID, filename: str, source_format: str
    ) -> None:
        if not filename:
            raise ValidationError(
                "Original filename cannot be empty.",
                error_code="filename_required",
            )
        if not source_format:
            raise ValidationError(
                "Source format cannot be empty.",
                error_code="source_format_required",
            )
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.",
                error_code="tenant_not_found",
            )

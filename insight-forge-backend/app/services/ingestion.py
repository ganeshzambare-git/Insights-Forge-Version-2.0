"""
Insight Forge V2 — Ingestion Service.

Coordinates raw dataset uploads: validate the file, stream it into storage,
register a ``Dataset`` row, and hand off to the cleaning worker. This service
stores bytes and metadata only — it never parses or cleans the file.
"""

from __future__ import annotations

import os
import uuid

from app.core.config import settings
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
from app.storage.base import StorageProvider, SupportsAsyncRead
from app.storage.exceptions import FileTooLargeError, StorageError


class IngestionService(BaseService):
    """Business service governing raw dataset ingestion."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
        storage: StorageProvider,
    ) -> None:
        """Initialize the IngestionService."""
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = DatasetRepository(session=uow.session)
        self.tenant_repo = TenantRepository(session=uow.session)
        self.storage = storage

    async def ingest_file(
        self,
        *,
        tenant_id: uuid.UUID,
        filename: str,
        source: SupportsAsyncRead,
    ) -> ServiceResult[Dataset]:
        """Validate, store, and register an uploaded dataset file.

        Args:
            tenant_id: Owning tenant UUID.
            filename: Original uploaded filename.
            source: Async-readable upload stream (e.g. FastAPI ``UploadFile``).

        Returns:
            A ServiceResult wrapping the created ``Dataset`` (status ``Pending``).
        """
        clean_name = (filename or "").strip()
        source_format = self._resolve_and_validate_format(clean_name)
        await self._validate_tenant(tenant_id)

        # Reserve the id up front so storage can key the object and the DB row
        # references the exact same identifier.
        dataset_id = self.uuid_provider.generate()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        # Stream to storage first (outside the DB transaction). This can be a
        # large, slow I/O operation and should not hold a DB lock open.
        try:
            stored = await self.storage.save(
                tenant_id=tenant_id,
                dataset_id=dataset_id,
                filename=clean_name,
                source=source,
                max_bytes=max_bytes,
            )
        except FileTooLargeError as exc:
            raise ValidationError(
                str(exc), error_code="file_too_large"
            ) from exc
        except StorageError as exc:
            raise ValidationError(
                f"Could not store uploaded file: {exc}",
                error_code="storage_failure",
            ) from exc

        async def action() -> Dataset:
            dataset = Dataset(
                dataset_id=dataset_id,
                tenant_id=tenant_id,
                original_filename=os.path.basename(clean_name) or clean_name,
                source_format=source_format,
                storage_uri=stored.uri,
                processing_status=DatasetStatus.PENDING.value,
                size_bytes=stored.size_bytes,
            )
            created = await self.repo.create(dataset)
            self.publish_domain_event(
                "DatasetIngested",
                {
                    "dataset_id": str(created.dataset_id),
                    "tenant_id": str(tenant_id),
                    "size_bytes": stored.size_bytes,
                },
            )
            return created

        try:
            return await self.execute_command(
                "ingest_dataset",
                action,
                success_msg=f"Dataset '{clean_name}' uploaded and queued for cleaning.",
            )
        except Exception:
            # DB registration failed — remove the orphaned file so storage and
            # the datasets table stay consistent.
            await self.storage.delete(stored.uri)
            raise

    # Private helpers
    def _resolve_and_validate_format(self, filename: str) -> str:
        if not filename:
            raise ValidationError(
                "A filename is required for the upload.",
                error_code="filename_required",
            )

        _, ext = os.path.splitext(filename)
        ext = ext.lstrip(".").lower()
        allowed = {e.lower() for e in settings.ALLOWED_UPLOAD_EXTENSIONS}
        if not ext or ext not in allowed:
            raise ValidationError(
                f"Unsupported file type '{ext or 'unknown'}'. "
                f"Allowed: {', '.join(sorted(allowed))}.",
                error_code="unsupported_file_type",
            )
        return ext

    async def _validate_tenant(self, tenant_id: uuid.UUID) -> None:
        if not await self.tenant_repo.exists(tenant_id=tenant_id):
            raise NotFoundError(
                f"Tenant '{tenant_id}' does not exist.",
                error_code="tenant_not_found",
            )

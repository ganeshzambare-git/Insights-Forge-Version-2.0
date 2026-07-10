"""
Insight Forge V2 — Data Cleaning Service.

Coordinates dataset quality analysis, format parsing, and trusted dataset certification.
"""

import uuid

from app.services.context import ServiceContext
from app.services.audit import DefaultAuditLogger
from app.services.providers import ClockProvider, UUIDProvider
from app.services.uow import UnitOfWork
from app.pipelines.cleaning_pipeline import CleaningPipeline
from app.ai.schemas.cleaning import CleaningLogEntry, TrustedDatasetSummary


class CleaningService:
    """Service layer managing the data cleaning pipeline execution lifecycle."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: DefaultAuditLogger,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the data cleaning service."""
        self.uow = uow
        self.context = context
        self.audit_logger = audit_logger
        self.clock = clock
        self.uuid = uuid_provider
        self.pipeline = CleaningPipeline()

    async def run_cleaning_pipeline(
        self,
        tenant_id: uuid.UUID,
        file_content: bytes,
        filename: str,
    ) -> tuple[TrustedDatasetSummary, list[CleaningLogEntry]]:
        """Coordinate validation, parser execution, and quality scoring."""
        # Standard logging of the command start
        service_name = self.__class__.__name__
        self.audit_logger.started(service_name, "run_cleaning_pipeline", self.context)
        
        try:
            summary, log_entries = await self.pipeline.execute(
                file_content=file_content, filename=filename
            )
            
            self.audit_logger.succeeded(
                service_name,
                "run_cleaning_pipeline",
                self.context,
                duration_ms=0.0,
                detail=f"Dataset {filename} cleaned successfully.",
            )

            return summary, log_entries
            
        except Exception as e:
            self.audit_logger.failed(
                service_name,
                "run_cleaning_pipeline",
                self.context,
                duration_ms=0.0,
                error=e,
            )
            raise

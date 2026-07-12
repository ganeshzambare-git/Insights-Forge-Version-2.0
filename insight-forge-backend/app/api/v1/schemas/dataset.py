"""
Insight Forge V2 — Dataset DTO Schemas.

Pydantic response models for uploaded datasets, their rows, and ingestion results.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetResponse(BaseModel):
    """Structured metadata for a stored dataset (matches the live schema)."""

    dataset_id: uuid.UUID = Field(..., description="Unique dataset UUID.")
    tenant_id: uuid.UUID = Field(..., description="Owning tenant UUID.")
    dataset_name: str = Field(..., description="Human-readable label derived from the filename.")
    original_filename: str = Field(..., description="Original uploaded filename.")
    source_format: str = Field(..., description="Detected source format (csv/json).")
    processing_status: str = Field(..., description="Lifecycle: Pending/Processing/Ready/Failed.")
    row_count: int | None = Field(default=None, description="Number of stored rows.")
    size_bytes: int | None = Field(default=None, description="Uploaded file size in bytes.")
    health_score: Decimal | None = Field(default=None, description="Data-quality score (0-100).")
    created_at: datetime = Field(..., description="Upload timestamp.")

    model_config = ConfigDict(from_attributes=True)


class IngestionResponse(BaseModel):
    """Result returned immediately after a successful upload."""

    dataset_id: uuid.UUID = Field(..., description="Identifier of the newly stored dataset.")
    dataset_name: str = Field(..., description="Human-readable dataset label.")
    row_count: int = Field(..., description="Number of rows ingested.")
    column_count: int = Field(..., description="Number of columns detected.")
    columns: list[str] = Field(default_factory=list, description="Ordered column headers.")
    processing_status: str = Field(..., description="Lifecycle status.")
    health_score: Decimal | None = Field(default=None, description="Data-quality score (0-100).")


class DatasetRecordResponse(BaseModel):
    """A single stored dataset row."""

    row_index: int = Field(..., description="Zero-based position in the original file.")
    payload: dict[str, Any] = Field(..., description="The row as a column->value mapping.")

    model_config = ConfigDict(from_attributes=True)

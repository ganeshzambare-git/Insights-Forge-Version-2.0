"""
Insight Forge V2 — Dataset DTO Schemas.

Defines Pydantic request and response models for Dataset operations.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.enums import DatasetStatus


class DatasetCreate(BaseModel):
    """Schema representing a dataset registration payload.

    This records dataset metadata only — the raw file bytes are streamed to
    object storage by the ingestion layer, not through this endpoint.
    """

    original_filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original filename of the uploaded dataset.",
        json_schema_extra={"example": "spring_2026_grades.csv"},
    )
    source_format: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="File format / source type of the dataset.",
        json_schema_extra={"example": "csv"},
    )
    size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Size of the uploaded file in bytes, if known.",
        json_schema_extra={"example": 1048576},
    )


class DatasetStatusUpdate(BaseModel):
    """Schema representing a dataset processing-status update (PATCH).

    Typically called by the cleaning worker to report progress and the final
    data health score once processing completes.
    """

    processing_status: DatasetStatus | None = Field(
        default=None,
        description="New processing status for the dataset.",
        json_schema_extra={"example": DatasetStatus.READY.value},
    )
    health_score: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Data-quality health score (0-100) produced by cleaning.",
        json_schema_extra={"example": 92.5},
    )
    row_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of cleaned rows written by the cleaning worker.",
        json_schema_extra={"example": 4200},
    )


class DatasetResponse(BaseModel):
    """Schema representing a structured dataset response payload."""

    dataset_id: uuid.UUID = Field(
        ..., description="Unique UUID primary key of the dataset."
    )
    tenant_id: uuid.UUID = Field(
        ..., description="UUID foreign key to the owning tenant partition."
    )
    original_filename: str = Field(..., description="Original uploaded filename.")
    source_format: str = Field(..., description="File format / source type.")
    processing_status: DatasetStatus = Field(
        ..., description="Current processing lifecycle status."
    )
    health_score: Decimal | None = Field(
        default=None, description="Data-quality health score (0-100), if computed."
    )
    row_count: int | None = Field(
        default=None, description="Cleaned row count, if computed."
    )
    size_bytes: int | None = Field(
        default=None, description="File size in bytes, if known."
    )
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last modification timestamp (UTC).")

    class Config:
        from_attributes = True

"""
Insight Forge V2 — Tenant DTO Schemas.

Defines Pydantic request and response models for Tenant operations.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    """Schema representing tenant partition creation payload."""

    tenant_slug: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="URL-friendly unique institutional identifier.",
        json_schema_extra={"example": "mit-university"},
    )
    tenant_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Institutional human-readable name.",
        json_schema_extra={"example": "MIT University"},
    )


class TenantUpdate(BaseModel):
    """Schema representing tenant partition modification payload (PATCH)."""

    tenant_slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=64,
        description="Updated unique institutional URL slug.",
        json_schema_extra={"example": "mit-university-east"},
    )
    tenant_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Updated human-readable name of the institution.",
        json_schema_extra={"example": "MIT University East"},
    )


class TenantResponse(BaseModel):
    """Schema representing structured tenant response payload."""

    tenant_id: uuid.UUID = Field(
        ..., description="Unique UUID primary key of the tenant."
    )
    tenant_slug: str = Field(..., description="Institutional slug identifier.")
    tenant_name: str = Field(..., description="Institutional human-readable name.")
    created_at: datetime = Field(..., description="Tenant creation timestamp.")

    model_config = ConfigDict(from_attributes=True)

"""
Insight Forge V2 — Cohort DTO Schemas.

Defines Pydantic request and response models for Cohort operations.
"""

import uuid
from pydantic import BaseModel, Field


class CohortCreate(BaseModel):
    """Schema representing cohort creation payload."""

    cohort_code: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Unique code identifying the cohort.",
        json_schema_extra={"example": "CS-2026"},
    )
    department_scope: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Department scope or institutional program name.",
        json_schema_extra={"example": "Computer Science"},
    )


class CohortUpdate(BaseModel):
    """Schema representing cohort modification payload (PATCH)."""

    cohort_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=64,
        description="Updated code of the cohort.",
        json_schema_extra={"example": "CS-2026-A"},
    )
    department_scope: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Updated department scope or program name of the cohort.",
        json_schema_extra={"example": "Computer Science & Engineering"},
    )


class CohortResponse(BaseModel):
    """Schema representing structured cohort response payload."""

    cohort_id: uuid.UUID = Field(
        ..., description="Unique UUID primary key of the cohort."
    )
    tenant_id: uuid.UUID = Field(
        ..., description="UUID foreign key to the tenant partition."
    )
    cohort_code: str = Field(..., description="Unique cohort code.")
    department_scope: str = Field(..., description="Department scope or program name.")

    class Config:
        from_attributes = True

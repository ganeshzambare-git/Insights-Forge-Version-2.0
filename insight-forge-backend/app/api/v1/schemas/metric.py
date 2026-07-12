"""
Insight Forge V2 — StudentMetric DTO Schemas.

Defines Pydantic request and response models for StudentMetric operations.
"""

from decimal import Decimal
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class StudentMetricCreate(BaseModel):
    """Schema representing academic performance metric logging payload."""

    student_id: uuid.UUID = Field(..., description="User UUID of the student record.")
    cohort_id: uuid.UUID = Field(
        ..., description="Cohort UUID of the student enrollment."
    )
    academic_year: str = Field(
        ...,
        min_length=4,
        max_length=32,
        description="Target academic year label.",
        json_schema_extra={"example": "2025-2026"},
    )
    gpa: Decimal = Field(
        ...,
        description="Academic GPA grade (scale 0.00 to 100.00).",
        json_schema_extra={"example": "85.50"},
    )
    attendance_rate: Decimal = Field(
        ...,
        description="Attendance percentage rate (scale 0.00 to 100.00).",
        json_schema_extra={"example": "92.00"},
    )
    status_indicator: str = Field(
        ...,
        description="Success indicator flag (Safe, Amber, Critical).",
        json_schema_extra={"example": "Safe"},
    )

    @field_validator("status_indicator")
    @classmethod
    def validate_status_indicator(cls, v: str) -> str:
        """Validate status indicator matches system status labels."""
        allowed = {"Safe", "Amber", "Critical"}
        if v not in allowed:
            raise ValueError(f"Status indicator must be one of: {allowed}")
        return v


class StudentMetricUpdate(BaseModel):
    """Schema representing academic performance metric modification payload (PATCH)."""

    academic_year: str | None = Field(
        default=None,
        min_length=4,
        max_length=32,
        description="Updated academic year label.",
    )
    gpa: Decimal | None = Field(default=None, description="Updated GPA grade.")
    attendance_rate: Decimal | None = Field(
        default=None, description="Updated attendance percentage."
    )
    status_indicator: str | None = Field(
        default=None, description="Updated status indicator flag."
    )

    @field_validator("status_indicator")
    @classmethod
    def validate_status_indicator(cls, v: str | None) -> str | None:
        """Validate status indicator matches system status labels if provided."""
        if v is None:
            return v
        allowed = {"Safe", "Amber", "Critical"}
        if v not in allowed:
            raise ValueError(f"Status indicator must be one of: {allowed}")
        return v


class StudentMetricResponse(BaseModel):
    """Schema representing structured student metric response payload."""

    metric_id: int = Field(
        ..., description="Unique ID primary key of the metric record."
    )
    tenant_id: uuid.UUID = Field(
        ..., description="UUID foreign key to the tenant partition."
    )
    student_id: uuid.UUID = Field(..., description="Student UUID.")
    cohort_id: uuid.UUID = Field(..., description="Cohort UUID.")
    academic_year: str = Field(..., description="Academic year label.")
    gpa: Decimal = Field(..., description="GPA grade.")
    attendance_rate: Decimal = Field(..., description="Attendance percentage.")
    status_indicator: str = Field(..., description="Status indicator flag.")

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("gpa", "attendance_rate")
    def serialize_decimal(self, value: Decimal) -> float:
        """Serialize Decimal fields as JSON floats for frontend consumption."""
        return float(value)

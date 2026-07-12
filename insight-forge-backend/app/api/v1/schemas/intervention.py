"""
Insight Forge V2 — CoachingIntervention DTO Schemas.

Defines Pydantic request and response models for CoachingIntervention operations.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class CoachingInterventionCreate(BaseModel):
    """Schema representing coaching intervention logging payload."""

    student_id: uuid.UUID = Field(
        ..., description="User UUID of the student receiving coaching."
    )
    advisor_id: uuid.UUID = Field(
        ..., description="User UUID of the advisor executing the intervention."
    )
    intervention_notes: str = Field(
        ...,
        min_length=2,
        description="Text notes summarizing the coaching discussions.",
        json_schema_extra={"example": "Discussed academic study plans."},
    )


class CoachingInterventionUpdate(BaseModel):
    """Schema representing coaching intervention modification payload (PATCH)."""

    intervention_notes: str | None = Field(
        default=None,
        min_length=2,
        description="Updated notes summarizing the coaching outcomes.",
        json_schema_extra={"example": "Updated notes with study guidelines."},
    )


class CoachingInterventionResponse(BaseModel):
    """Schema representing structured coaching intervention response payload."""

    intervention_id: uuid.UUID = Field(
        ..., description="Unique UUID primary key of the intervention log."
    )
    tenant_id: uuid.UUID = Field(
        ..., description="UUID foreign key to the tenant partition."
    )
    student_id: uuid.UUID = Field(..., description="Student UUID.")
    advisor_id: uuid.UUID = Field(..., description="Advisor/Faculty UUID.")
    intervention_notes: str = Field(..., description="Intervention notes.")
    logged_at: datetime = Field(..., description="Intervention logging timestamp.")

    model_config = ConfigDict(from_attributes=True)

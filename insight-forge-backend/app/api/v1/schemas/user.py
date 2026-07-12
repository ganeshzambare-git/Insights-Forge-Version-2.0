"""
Insight Forge V2 — User DTO Schemas.

Defines Pydantic request and response models for User operations.
"""

import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.roles import Role


class UserCreate(BaseModel):
    """Schema representing user registration payload."""

    corporate_email: EmailStr = Field(
        ...,
        description="Unique corporate email address.",
        json_schema_extra={"example": "dean.jones@mit-edu.org"},
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Raw login password. Enforces system complexity rules.",
        json_schema_extra={"example": "StrongPass123!"},
    )
    assigned_role: Role = Field(
        ...,
        description="System role. Must match allowed PascalCase database values.",
        json_schema_extra={"example": "Dean"},
    )


class UserUpdate(BaseModel):
    """Schema representing user account modification payload (PATCH)."""

    assigned_role: Role | None = Field(
        default=None,
        description="Updated system role.",
        json_schema_extra={"example": "Faculty"},
    )
    is_mfa_enabled: bool | None = Field(
        default=None,
        description="MFA enablement flag status.",
        json_schema_extra={"example": True},
    )


class UserResponse(BaseModel):
    """Schema representing structured user response payload (excluding hashes)."""

    user_id: uuid.UUID = Field(..., description="Unique UUID primary key of the user.")
    tenant_id: uuid.UUID = Field(
        ..., description="UUID foreign key to the tenant partition."
    )
    corporate_email: str = Field(..., description="Corporate email address.")
    assigned_role: str = Field(..., description="Assigned role string.")
    is_mfa_enabled: bool = Field(..., description="True if MFA is enabled.")

    model_config = ConfigDict(from_attributes=True)

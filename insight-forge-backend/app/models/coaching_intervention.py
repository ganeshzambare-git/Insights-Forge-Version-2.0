"""
Insight Forge V2 — Coaching Intervention ORM Model.

Defines the database model representing institutional academic intervention events.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types.encrypted import EncryptedString


class CoachingIntervention(Base):
    """Educational coaching intervention logged for a student."""

    __tablename__ = "coaching_interventions"

    intervention_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )

    student_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )

    faculty_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )

    intervention_notes: Mapped[str] = mapped_column(
        EncryptedString(1000),
        nullable=False,
    )

    recorded_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        Index(
            "ix_coaching_interventions_tenant_student_recorded",
            "recorded_timestamp",
            "student_user_id",
            "tenant_id",
        ),
    )

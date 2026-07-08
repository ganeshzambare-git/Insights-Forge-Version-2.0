from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentMetric(Base):
    __tablename__ = "student_metrics"

    metric_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "tenants.tenant_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    student_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.user_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cohorts.cohort_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    raw_average_grade: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
    )

    normalized_grade_score: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )

    attendance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
    )

    success_indicator_status: Mapped[str] = mapped_column(
        String(length=24),
        nullable=False,
    )

    reporting_period: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "success_indicator_status IN "
            "('Safe', 'Amber', 'Critical')",
            name="success_indicator_status",
        ),
        CheckConstraint(
            "attendance_percentage >= 0 "
            "AND attendance_percentage <= 100.00",
            name="attendance_percentage_range",
        ),
        CheckConstraint(
            "raw_average_grade >= 0 "
            "AND raw_average_grade <= 100.00",
            name="raw_average_grade_range",
        ),
        Index(
            "ix_student_metrics_tenant_cohort_status",
            "tenant_id",
            "cohort_id",
            "success_indicator_status",
        ),
        Index(
            "ix_student_metrics_tenant_grade",
            "tenant_id",
            normalized_grade_score.desc(),
        ),
    )
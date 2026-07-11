"""
Insight Forge V2 — Dataset Model.

Represents a raw dataset uploaded by a tenant and tracked through the
ingestion/cleaning lifecycle. The backend stores metadata only; the actual
file bytes and cleaning logic live outside this ORM record.
"""

import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import DatasetStatus
from app.db.base import Base
from app.models.mixins.timestamp import TimestampMixin


class Dataset(Base, TimestampMixin):
    """Tenant-scoped record describing an uploaded dataset and its processing state."""

    __tablename__ = "datasets"

    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('Pending', 'Processing', 'Ready', 'Failed')",
            name="ck_datasets_processing_status",
        ),
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_format: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    storage_uri: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    processing_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text(f"'{DatasetStatus.PENDING.value}'"),
    )

    health_score: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )

    row_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

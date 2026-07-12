from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Identity, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins.timestamp import TimestampMixin


class Dataset(Base, TimestampMixin):
    """An uploaded dataset, tracked per tenant.

    Schema matches the live ``datasets`` table exactly (processing_status,
    size_bytes, storage_uri) so this backend runs against the existing database.
    """

    __tablename__ = "datasets"

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

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_format: Mapped[str] = mapped_column(String(32), nullable=False)

    # Lifecycle: Pending | Processing | Ready | Failed (DB CHECK enforced).
    processing_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'Pending'")
    )

    health_score: Mapped[Decimal | None] = mapped_column(Numeric(), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    @property
    def dataset_name(self) -> str:
        """Human-readable label derived from the uploaded filename."""
        name = self.original_filename or ""
        return name.rsplit(".", 1)[0] if "." in name else name


class DatasetRecord(Base):
    """A single row of an uploaded dataset, stored generically as JSONB.

    Additive table (not present in the original schema) that lets stored uploads
    be re-analysed by the deterministic pipeline without external object storage.
    """

    __tablename__ = "dataset_records"

    record_id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.dataset_id", ondelete="CASCADE"),
        nullable=False,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )

    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        Index("ix_dataset_records_dataset_id_row_index", "dataset_id", "row_index"),
    )

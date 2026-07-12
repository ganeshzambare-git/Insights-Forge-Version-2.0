"""add datasets and dataset_records tables

Revision ID: b1a2c3d4e5f6
Revises: 9092070a0ca7
Create Date: 2026-07-11 00:00:00.000000

Note: the live Neon database already contains a ``datasets`` table (created by a
newer sibling codebase) but NOT ``dataset_records``. Against that database only
the ``dataset_records`` half is applied out-of-band (see scripts/create dataset
records). This migration is the canonical definition for a clean database and
mirrors the live ``datasets`` schema exactly so both stay compatible.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9092070a0ca7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("dataset_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("source_format", sa.String(length=32), nullable=False),
        sa.Column("processing_status", sa.String(length=24), server_default=sa.text("'Pending'"), nullable=False),
        sa.Column("health_score", sa.Numeric(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("storage_uri", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "processing_status IN ('Pending', 'Processing', 'Ready', 'Failed')",
            name=op.f("ck_datasets_processing_status"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"], name=op.f("fk_datasets_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("dataset_id", name=op.f("pk_datasets")),
    )

    op.create_table(
        "dataset_records",
        sa.Column("record_id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("dataset_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.dataset_id"], name=op.f("fk_dataset_records_dataset_id_datasets"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.tenant_id"], name=op.f("fk_dataset_records_tenant_id_tenants"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("record_id", name=op.f("pk_dataset_records")),
    )
    op.create_index("ix_dataset_records_dataset_id_row_index", "dataset_records", ["dataset_id", "row_index"], unique=False)

    # Enable Row Level Security with tenant isolation, mirroring the strict tables.
    for table in ("datasets", "dataset_records"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY tenant_isolation_policy ON {table} "
            f"USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);"
        )


def downgrade() -> None:
    for table in ("dataset_records", "datasets"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_dataset_records_dataset_id_row_index", table_name="dataset_records")
    op.drop_table("dataset_records")
    op.drop_table("datasets")

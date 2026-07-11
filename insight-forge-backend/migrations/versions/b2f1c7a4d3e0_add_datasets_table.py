"""add_datasets_table

Adds the tenant-scoped ``datasets`` table used to track uploaded datasets
through the ingestion/cleaning lifecycle, with Row-Level Security enforcing
tenant isolation.

Revision ID: b2f1c7a4d3e0
Revises: 9092070a0ca7
Create Date: 2026-07-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f1c7a4d3e0"
down_revision: Union[str, Sequence[str], None] = "9092070a0ca7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column(
            "dataset_id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("source_format", sa.String(length=32), nullable=False),
        sa.Column(
            "processing_status",
            sa.String(length=24),
            server_default=sa.text("'Pending'"),
            nullable=False,
        ),
        sa.Column("health_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "processing_status IN ('Pending', 'Processing', 'Ready', 'Failed')",
            name=op.f("ck_datasets_processing_status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            name=op.f("fk_datasets_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("dataset_id", name=op.f("pk_datasets")),
    )
    op.create_index(
        "ix_datasets_tenant_created",
        "datasets",
        ["tenant_id", sa.literal_column("created_at DESC")],
        unique=False,
    )

    # Enable Row Level Security with strict tenant isolation
    op.execute("ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON datasets "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON datasets;")
    op.execute("ALTER TABLE datasets DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_datasets_tenant_created", table_name="datasets")
    op.drop_table("datasets")

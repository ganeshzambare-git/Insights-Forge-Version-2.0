"""add_tasks_and_budgets

Adds tenant-scoped ``background_tasks`` (job lifecycle tracking for FastAPI
BackgroundTasks) and ``budget_allocations`` (finance dashboard) tables, both
with Row-Level Security tenant isolation.

Revision ID: d4e6f9a1b2c7
Revises: c3a2d5b8e1f4
Create Date: 2026-07-11 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4e6f9a1b2c7"
down_revision: Union[str, Sequence[str], None] = "c3a2d5b8e1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
    op.execute(
        f"CREATE POLICY tenant_isolation_policy ON {table} "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);"
    )


def upgrade() -> None:
    op.create_table(
        "background_tasks",
        sa.Column(
            "task_id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=24),
            server_default=sa.text("'Pending'"),
            nullable=False,
        ),
        sa.Column(
            "progress_pct", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "timeline",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            "status IN ('Pending', 'Running', 'Completed', 'Failed')",
            name=op.f("ck_background_tasks_status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            name=op.f("fk_background_tasks_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_background_tasks")),
    )
    op.create_index(
        "ix_background_tasks_tenant_created",
        "background_tasks",
        ["tenant_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    _enable_rls("background_tasks")

    op.create_table(
        "budget_allocations",
        sa.Column(
            "allocation_id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("dimension", sa.String(length=128), nullable=False),
        sa.Column("fiscal_year", sa.String(length=16), nullable=False),
        sa.Column("allocated_budget", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("current_balance", sa.Numeric(precision=14, scale=2), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            name=op.f("fk_budget_allocations_tenant_id_tenants"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("allocation_id", name=op.f("pk_budget_allocations")),
    )
    op.create_index(
        "ix_budget_allocations_tenant",
        "budget_allocations",
        ["tenant_id"],
        unique=False,
    )
    _enable_rls("budget_allocations")


def downgrade() -> None:
    for table in ("budget_allocations", "background_tasks"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_budget_allocations_tenant", table_name="budget_allocations")
    op.drop_table("budget_allocations")
    op.drop_index("ix_background_tasks_tenant_created", table_name="background_tasks")
    op.drop_table("background_tasks")

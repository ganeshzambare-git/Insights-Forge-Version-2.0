"""enable tenant row level security

Revision ID: c0e1fca26f23
Revises: 2f1b40cac3be
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c0e1fca26f23"
down_revision: Union[str, Sequence[str], None] = "2f1b40cac3be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TENANT_TABLES = (
    "users",
    "sessions",
    "cohorts",
    "student_metrics",
    "coaching_interventions",
)


def upgrade() -> None:
    for table_name in TENANT_TABLES:
        op.execute(
            f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'
        )

        op.execute(
            f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'
        )

        op.execute(
            f"""
            CREATE POLICY {table_name}_tenant_isolation
            ON "{table_name}"
            FOR ALL
            USING (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(
                    current_setting(
                        'app.current_tenant_id',
                        true
                    ),
                    ''
                )::uuid
            )
            """
        )


def downgrade() -> None:
    for table_name in reversed(TENANT_TABLES):
        op.execute(
            f"""
            DROP POLICY IF EXISTS
            {table_name}_tenant_isolation
            ON "{table_name}"
            """
        )

        op.execute(
            f'ALTER TABLE "{table_name}" NO FORCE ROW LEVEL SECURITY'
        )

        op.execute(
            f'ALTER TABLE "{table_name}" DISABLE ROW LEVEL SECURITY'
        )
"""add_dataset_storage_uri

Adds a nullable ``storage_uri`` column to ``datasets`` recording where the raw
uploaded file was persisted by the ingestion layer.

Revision ID: c3a2d5b8e1f4
Revises: b2f1c7a4d3e0
Create Date: 2026-07-11 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a2d5b8e1f4"
down_revision: Union[str, Sequence[str], None] = "b2f1c7a4d3e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column("storage_uri", sa.String(length=1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("datasets", "storage_uri")

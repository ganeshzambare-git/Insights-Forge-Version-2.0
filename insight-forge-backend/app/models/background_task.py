"""
Insight Forge V2 — Background Task Model.

Persists the lifecycle of long-running jobs executed via FastAPI
``BackgroundTasks`` (no Celery/Redis). Handlers create a row, update its
progress/timeline as work proceeds, and mark it Completed/Failed. The
``/tasks`` endpoints read these rows — the data is real, not mocked.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import TaskStatus
from app.db.base import Base
from app.models.mixins.timestamp import TimestampMixin


class BackgroundTask(Base, TimestampMixin):
    """Tenant-scoped record tracking a background job's execution."""

    __tablename__ = "background_tasks"

    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Running', 'Completed', 'Failed')",
            name="ck_background_tasks_status",
        ),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )

    task_type: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text(f"'{TaskStatus.PENDING.value}'"),
    )

    progress_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )

    timeline: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

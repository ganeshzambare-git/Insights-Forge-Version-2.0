"""
Insight Forge V2 — Cleaning Handoff Trigger.

The ingestion layer stores the raw file and then *hands off* to the separate
cleaning worker — it never parses or cleans the data itself. Since this MVP has
no Celery/queue, the handoff runs as a FastAPI background task that flips the
dataset from ``Pending`` to ``Processing`` and logs the notification. The actual
cleaning (imputation, outlier detection, etc.) is owned by the Data Analyst and
lives outside this service.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.enums import DatasetStatus, TaskStatus
from app.db.session import async_session_maker
from app.models.background_task import BackgroundTask

logger = logging.getLogger("app.ingestion.trigger")


async def trigger_cleaning(dataset_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
    """Notify the cleaning worker that a new dataset is ready to process.

    Opens its own short-lived session (the request session is already closed by
    the time this background task runs), marks the dataset ``Processing``, and
    records a real ``background_tasks`` row for the handoff so it appears on the
    task monitor. No Celery — this runs via FastAPI BackgroundTasks.

    Args:
        dataset_id: The freshly ingested dataset.
        tenant_id: Owning tenant, required so the update passes RLS.
    """
    try:
        now = datetime.now(timezone.utc)
        async with async_session_maker() as session:
            # Scope the transaction to the tenant so RLS permits the writes.
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(tenant_id)},
            )
            await session.execute(
                text(
                    "UPDATE datasets SET processing_status = :status "
                    "WHERE dataset_id = :did AND processing_status = :pending"
                ),
                {
                    "status": DatasetStatus.PROCESSING.value,
                    "did": str(dataset_id),
                    "pending": DatasetStatus.PENDING.value,
                },
            )

            # Record the handoff as a real background task.
            session.add(
                BackgroundTask(
                    task_id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    task_type="DATA_INGESTION",
                    status=TaskStatus.RUNNING.value,
                    progress_pct=10,
                    started_at=now,
                    timeline=[
                        {"event": "Queued", "timestamp": now.isoformat()},
                        {
                            "event": f"Cleaning handoff for dataset {dataset_id}",
                            "timestamp": now.isoformat(),
                        },
                    ],
                )
            )
            await session.commit()
        logger.info(
            "Cleaning worker notified for dataset %s (tenant %s)",
            dataset_id,
            tenant_id,
        )
    except Exception:  # never let a handoff failure crash the request lifecycle
        logger.exception("Failed to trigger cleaning for dataset %s", dataset_id)

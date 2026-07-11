"""
Insight Forge V2 — Core Domain Enumerations.

Shared string enums used across models, schemas, and services.
"""

from enum import Enum


class DatasetStatus(str, Enum):
    """Lifecycle status of an uploaded dataset as it moves through ingestion/cleaning."""

    PENDING = "Pending"
    PROCESSING = "Processing"
    READY = "Ready"
    FAILED = "Failed"

    @classmethod
    def values(cls) -> list[str]:
        """Return all status string values (useful for SQL CHECK constraints)."""
        return [member.value for member in cls]


class TaskStatus(str, Enum):
    """Lifecycle status of a background task run via FastAPI BackgroundTasks."""

    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"

    @classmethod
    def values(cls) -> list[str]:
        """Return all status string values (useful for SQL CHECK constraints)."""
        return [member.value for member in cls]

"""
Insight Forge V2 — Repositories Entrypoint.

Binds and exposes all active domain data-access repositories.
"""

from app.repositories.exceptions import (
    DuplicateEntryError,
    EntityNotFoundError,
    RepositoryError,
)
from app.repositories.base import BaseRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.repositories.session import SessionRepository
from app.repositories.cohort import CohortRepository
from app.repositories.student_metric import StudentMetricRepository
from app.repositories.coaching_intervention import CoachingInterventionRepository

__all__ = [
    "DuplicateEntryError",
    "EntityNotFoundError",
    "RepositoryError",
    "BaseRepository",
    "TenantRepository",
    "UserRepository",
    "SessionRepository",
    "CohortRepository",
    "StudentMetricRepository",
    "CoachingInterventionRepository",
]

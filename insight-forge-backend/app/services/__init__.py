"""
Insight Forge V2 — Service Layer Packages.

Exports service boundary classes, context structures, result envelopes, and exceptions.
"""

from app.services.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolation,
    ConflictError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from app.services.context import ServiceContext
from app.services.result import (
    PaginationParams,
    PaginationResult,
    ServiceResult,
)
from app.services.providers import (
    ClockProvider,
    SystemClockProvider,
    SystemUUIDProvider,
    UUIDProvider,
)
from app.services.uow import UnitOfWork
from app.services.audit import AuditLoggerProtocol, DefaultAuditLogger
from app.services.base import BaseService

# Domain services stubs
from app.services.tenant import TenantService
from app.services.user import UserService
from app.services.session import SessionService
from app.services.cohort import CohortService
from app.services.student_metric import StudentMetricService
from app.services.coaching_intervention import CoachingInterventionService
from app.services.auth import AuthService
from app.services.dataset import DatasetService
from app.services.ingestion import IngestionService
from app.services.task_service import TaskService
from app.services.finance_service import FinanceService

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleViolation",
    "ConflictError",
    "NotFoundError",
    "ServiceError",
    "ValidationError",
    "ServiceContext",
    "PaginationParams",
    "PaginationResult",
    "ServiceResult",
    "ClockProvider",
    "SystemClockProvider",
    "SystemUUIDProvider",
    "UUIDProvider",
    "UnitOfWork",
    "AuditLoggerProtocol",
    "DefaultAuditLogger",
    "BaseService",
    "TenantService",
    "UserService",
    "SessionService",
    "CohortService",
    "StudentMetricService",
    "CoachingInterventionService",
    "AuthService",
    "DatasetService",
    "IngestionService",
    "TaskService",
    "FinanceService",
]

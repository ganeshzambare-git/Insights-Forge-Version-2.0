"""
Insight Forge V2 — Service Dependencies.

Declares factory functions for injecting services and their repository/UoW dependencies.
"""

import uuid
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.audit import DefaultAuditLogger
from app.services.context import ServiceContext
from app.services.providers import SystemClockProvider, SystemUUIDProvider
from app.services.uow import UnitOfWork

# Services
from app.services.tenant import TenantService
from app.services.user import UserService
from app.services.session import SessionService
from app.services.cohort import CohortService
from app.services.student_metric import StudentMetricService
from app.services.coaching_intervention import CoachingInterventionService
from app.services.auth import AuthService
from app.services.analytics import AnalyticsService
from app.services.dataset import DatasetService


def get_service_context(request: Request) -> ServiceContext:
    """FastAPI dependency to extract request context and JWT metadata."""
    request_id = getattr(request.state, "request_id", "unknown-req-id")
    user_id = None
    tenant_id = None
    role = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from app.core.security import decode_token

            payload = decode_token(token)
            if payload.get("sub"):
                user_id = uuid.UUID(payload["sub"])
            if payload.get("tenant_id"):
                tenant_id = uuid.UUID(payload["tenant_id"])
            role = payload.get("role")
        except Exception:
            pass

    return ServiceContext(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
        request_id=request_id,
    )


def get_uow(session: AsyncSession = Depends(get_async_session)) -> UnitOfWork:
    """FastAPI dependency to provide a UnitOfWork transaction manager."""
    return UnitOfWork(session=session)


def get_tenant_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> TenantService:
    """Construct and inject a TenantService."""
    return TenantService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_user_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> UserService:
    """Construct and inject a UserService."""
    return UserService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_session_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> SessionService:
    """Construct and inject a SessionService."""
    return SessionService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_cohort_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> CohortService:
    """Construct and inject a CohortService."""
    return CohortService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_student_metric_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> StudentMetricService:
    """Construct and inject a StudentMetricService."""
    return StudentMetricService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_coaching_intervention_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> CoachingInterventionService:
    """Construct and inject a CoachingInterventionService."""
    return CoachingInterventionService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_auth_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> AuthService:
    """Construct and inject an AuthService."""
    return AuthService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_analytics_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> AnalyticsService:
    """Construct and inject an AnalyticsService."""
    return AnalyticsService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_dataset_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> DatasetService:
    """Construct and inject a DatasetService."""
    return DatasetService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


from app.services.ai_service import AIService  # noqa: E402
from app.services.cleaning import CleaningService  # noqa: E402

def get_ai_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> AIService:
    """Construct and inject an AIService."""
    return AIService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )


def get_cleaning_service(
    uow: UnitOfWork = Depends(get_uow),
    context: ServiceContext = Depends(get_service_context),
) -> CleaningService:
    """Construct and inject a CleaningService."""
    return CleaningService(
        uow=uow,
        context=context,
        audit_logger=DefaultAuditLogger(),
        clock=SystemClockProvider(),
        uuid_provider=SystemUUIDProvider(),
    )



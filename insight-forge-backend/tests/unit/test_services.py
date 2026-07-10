"""
Insight Forge V2 — Service Layer Infrastructure Unit Tests.

Validates transaction boundary controls, audit triggers, exception propagation, and nested scopes.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.exceptions import ServiceError, ValidationError, ConflictError
from app.services.base import BaseService
from app.services import (
    TenantService,
    UserService,
    SessionService,
    CohortService,
    StudentMetricService,
    CoachingInterventionService,
)


class DummyService(BaseService):
    """Test service extending BaseService to validate infrastructure behaviors."""

    async def successful_command(self) -> str:
        async def action() -> str:
            return "ok"

        result = await self.execute_command(
            "successful_command",
            action,
            "Successfully completed dummy command",
        )
        return result.data

    async def failing_command_domain_error(self) -> None:
        async def action() -> None:
            raise ValidationError("Domain rule failed", error_code="dummy_error")

        await self.execute_command("failing_command_domain_error", action)

    async def failing_command_unexpected_error(self) -> None:
        async def action() -> None:
            raise RuntimeError("Database connection lost")

        await self.execute_command("failing_command_unexpected_error", action)


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock AsyncSession instance."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_audit_logger() -> MagicMock:
    """Mock audit logging engine."""
    return MagicMock()


@pytest.fixture
def mock_clock() -> MagicMock:
    """Mock Clock provider."""
    return MagicMock()


@pytest.fixture
def mock_uuid_provider() -> MagicMock:
    """Mock UUID provider."""
    return MagicMock()


@pytest.fixture
def context() -> ServiceContext:
    """Mock execution context."""
    return ServiceContext(request_id="req-123", role="Admin")


@pytest.mark.anyio
async def test_uow_commit_on_success(mock_session: AsyncMock) -> None:
    """Verify that UnitOfWork commits only at the outermost scope on success."""
    uow = UnitOfWork(mock_session)
    async with uow:
        # Inner scope
        async with uow:
            pass
        # Assert commit is not called yet
        mock_session.commit.assert_not_called()

    # Outer scope exits, commit is called
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.anyio
async def test_uow_rollback_on_exception(mock_session: AsyncMock) -> None:
    """Verify that UnitOfWork rolls back immediately on any exception."""
    uow = UnitOfWork(mock_session)
    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("Failure in execution")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


@pytest.mark.anyio
async def test_service_successful_lifecycle(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify successful BaseService.execute_command logs start/success, commits, and returns ServiceResult."""
    uow = UnitOfWork(mock_session)
    service = DummyService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )

    result_data = await service.successful_command()

    assert result_data == "ok"
    # Verify transaction committed
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()

    # Verify audit logger hooks
    mock_audit_logger.started.assert_called_once_with(
        "DummyService", "successful_command", context
    )
    mock_audit_logger.succeeded.assert_called_once()
    mock_audit_logger.failed.assert_not_called()


@pytest.mark.anyio
async def test_service_lifecycle_domain_exception(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify BaseService.execute_command rolls back, logs failed event, and propagates domain errors."""
    uow = UnitOfWork(mock_session)
    service = DummyService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )

    with pytest.raises(ValidationError) as excinfo:
        await service.failing_command_domain_error()

    assert excinfo.value.error_code == "dummy_error"
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()

    mock_audit_logger.started.assert_called_once_with(
        "DummyService", "failing_command_domain_error", context
    )
    mock_audit_logger.failed.assert_called_once()
    mock_audit_logger.succeeded.assert_not_called()


@pytest.mark.anyio
async def test_service_lifecycle_unexpected_exception(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify generic exceptions are mapped to ServiceError with unexpected_error code."""
    uow = UnitOfWork(mock_session)
    service = DummyService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )

    with pytest.raises(ServiceError) as excinfo:
        await service.failing_command_unexpected_error()

    assert excinfo.value.error_code == "unexpected_error"
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()

    mock_audit_logger.started.assert_called_once_with(
        "DummyService", "failing_command_unexpected_error", context
    )
    mock_audit_logger.failed.assert_called_once()


# Domain Services Tests


@pytest.mark.anyio
async def test_tenant_service_create_success(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify successful tenant creation."""
    uow = UnitOfWork(mock_session)
    service = TenantService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.repo.slug_exists = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(side_effect=lambda x: x)

    mock_uuid = uuid.uuid4()
    mock_uuid_provider.generate.return_value = mock_uuid
    mock_now = datetime.now(timezone.utc)
    mock_clock.now.return_value = mock_now

    res = await service.create_tenant(slug="Test Tenant ", name="  Test School ")
    assert res.success is True
    assert res.data.tenant_slug == "test-tenant"
    assert res.data.tenant_name == "Test School"
    assert res.data.tenant_id == mock_uuid
    assert res.data.created_at == mock_now


@pytest.mark.anyio
async def test_tenant_service_create_duplicate_conflict(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify duplicate tenant slug creation raises ConflictError."""
    uow = UnitOfWork(mock_session)
    service = TenantService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.repo.slug_exists = AsyncMock(return_value=True)

    with pytest.raises(ConflictError) as exc:
        await service.create_tenant(slug="duplicate", name="Test Name")
    assert exc.value.error_code == "slug_conflict"


@pytest.mark.anyio
async def test_user_service_create_success(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify successful user creation and parameters mapping."""
    uow = UnitOfWork(mock_session)
    service = UserService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.tenant_repo = MagicMock()

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.repo.email_exists = AsyncMock(return_value=False)
    service.repo.create = AsyncMock(side_effect=lambda x: x)

    tenant_id = uuid.uuid4()
    user_uuid = uuid.uuid4()
    mock_uuid_provider.generate.return_value = user_uuid

    res = await service.create_user(
        tenant_id=tenant_id,
        email=" TEST@school.edu ",
        password_hash="hashed_string",
        role="Faculty",
    )
    assert res.success is True
    assert res.data.corporate_email == "test@school.edu"
    assert res.data.assigned_role == "Faculty"
    assert res.data.user_id == user_uuid


@pytest.mark.anyio
async def test_user_service_create_invalid_role(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify invalid user roles raise ValidationError."""
    uow = UnitOfWork(mock_session)
    service = UserService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )

    with pytest.raises(ValidationError) as exc:
        await service.create_user(
            tenant_id=uuid.uuid4(),
            email="test@test.com",
            password_hash="hash",
            role="Superuser",
        )
    assert exc.value.error_code == "invalid_role"


@pytest.mark.anyio
async def test_session_service_create_success(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify login session creation."""
    uow = UnitOfWork(mock_session)
    service = SessionService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.user_repo = MagicMock()
    service.tenant_repo = MagicMock()

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    mock_user = MagicMock()
    mock_user.tenant_id = tenant_id

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.user_repo.get_by_id = AsyncMock(return_value=mock_user)
    service.repo.get_by_jti = AsyncMock(return_value=None)
    service.repo.create = AsyncMock(side_effect=lambda x: x)

    mock_now = datetime.now(timezone.utc)
    mock_clock.now.return_value = mock_now
    expiry = datetime(2030, 1, 1, tzinfo=timezone.utc)

    res = await service.create_session(
        user_id=user_id,
        tenant_id=tenant_id,
        jwt_jti="unique-jti",
        expires_at=expiry,
        ingress_ip="127.0.0.1",
    )
    assert res.success is True
    assert res.data.jwt_jti == "unique-jti"
    assert res.data.user_id == user_id


@pytest.mark.anyio
async def test_session_service_user_tenant_mismatch(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify mismatched user/tenant IDs raises ValidationError."""
    uow = UnitOfWork(mock_session)
    service = SessionService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.user_repo = MagicMock()
    service.tenant_repo = MagicMock()

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    mock_user = MagicMock()
    mock_user.tenant_id = uuid.uuid4()  # Mismatched tenant ID

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.user_repo.get_by_id = AsyncMock(return_value=mock_user)

    mock_clock.now.return_value = datetime.now(timezone.utc)

    with pytest.raises(ValidationError) as exc:
        await service.create_session(
            user_id=user_id,
            tenant_id=tenant_id,
            jwt_jti="test-jti",
            expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
            ingress_ip="127.0.0.1",
        )
    assert exc.value.error_code == "user_tenant_mismatch"


@pytest.mark.anyio
async def test_cohort_service_create_success(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify cohort code creation rules."""
    uow = UnitOfWork(mock_session)
    service = CohortService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.tenant_repo = MagicMock()

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.repo.get_by_code = AsyncMock(return_value=None)
    service.repo.create = AsyncMock(side_effect=lambda x: x)

    tenant_id = uuid.uuid4()
    res = await service.create_cohort(
        tenant_id=tenant_id, cohort_code=" cs-101 ", department_scope=" CS "
    )
    assert res.success is True
    assert res.data.cohort_code == "CS-101"
    assert res.data.department_scope == "CS"


@pytest.mark.anyio
async def test_student_metric_service_add_success(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify student performance metric creation validation."""
    uow = UnitOfWork(mock_session)
    service = StudentMetricService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.user_repo = MagicMock()
    service.cohort_repo = MagicMock()
    service.tenant_repo = MagicMock()

    tenant_id = uuid.uuid4()
    student_id = uuid.uuid4()
    cohort_id = uuid.uuid4()

    mock_student = MagicMock()
    mock_student.tenant_id = tenant_id
    mock_student.assigned_role = "Student"

    mock_cohort = MagicMock()
    mock_cohort.tenant_id = tenant_id

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.user_repo.get_by_id = AsyncMock(return_value=mock_student)
    service.cohort_repo.get_by_id = AsyncMock(return_value=mock_cohort)
    service.repo.create = AsyncMock(side_effect=lambda x: x)

    res = await service.add_metric(
        tenant_id=tenant_id,
        student_user_id=student_id,
        cohort_id=cohort_id,
        raw_average_grade=Decimal("92.50"),
        normalized_grade_score=Decimal("4.0"),
        attendance_percentage=Decimal("98.00"),
        success_indicator_status="Safe",
        reporting_period="Term-1",
    )
    assert res.success is True
    assert res.data.raw_average_grade == Decimal("92.50")
    assert res.data.success_indicator_status == "Safe"


@pytest.mark.anyio
async def test_student_metric_service_invalid_grade_range(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify grade averages exceeding 100.00 raises ValidationError."""
    uow = UnitOfWork(mock_session)
    service = StudentMetricService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )

    with pytest.raises(ValidationError) as exc:
        await service.add_metric(
            tenant_id=uuid.uuid4(),
            student_user_id=uuid.uuid4(),
            cohort_id=uuid.uuid4(),
            raw_average_grade=Decimal("105.00"),  # Out of range
            normalized_grade_score=None,
            attendance_percentage=Decimal("90.00"),
            success_indicator_status="Safe",
            reporting_period="Term-1",
        )
    assert exc.value.error_code == "invalid_grade"


@pytest.mark.anyio
async def test_coaching_intervention_service_create_success(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify student coaching intervention creation validations."""
    uow = UnitOfWork(mock_session)
    service = CoachingInterventionService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.user_repo = MagicMock()
    service.tenant_repo = MagicMock()

    tenant_id = uuid.uuid4()
    student_id = uuid.uuid4()
    faculty_id = uuid.uuid4()

    mock_student = MagicMock()
    mock_student.tenant_id = tenant_id
    mock_student.assigned_role = "Student"

    mock_faculty = MagicMock()
    mock_faculty.tenant_id = tenant_id
    mock_faculty.assigned_role = "Faculty"

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.user_repo.get_by_id = AsyncMock(
        side_effect=lambda x: mock_student if x == student_id else mock_faculty
    )
    service.repo.create = AsyncMock(side_effect=lambda x: x)

    res = await service.create_intervention(
        tenant_id=tenant_id,
        student_user_id=student_id,
        faculty_user_id=faculty_id,
        intervention_notes="Excellent coaching session",
    )
    assert res.success is True
    assert res.data.intervention_notes == "Excellent coaching session"


@pytest.mark.anyio
async def test_coaching_intervention_service_invalid_faculty_role(
    mock_session: AsyncMock,
    mock_audit_logger: MagicMock,
    mock_clock: MagicMock,
    mock_uuid_provider: MagicMock,
    context: ServiceContext,
) -> None:
    """Verify only faculty/deans can log interventions."""
    uow = UnitOfWork(mock_session)
    service = CoachingInterventionService(
        uow, context, mock_audit_logger, mock_clock, mock_uuid_provider
    )
    service.repo = MagicMock()
    service.user_repo = MagicMock()
    service.tenant_repo = MagicMock()

    tenant_id = uuid.uuid4()
    student_id = uuid.uuid4()
    faculty_id = uuid.uuid4()

    mock_student = MagicMock()
    mock_student.tenant_id = tenant_id
    mock_student.assigned_role = "Student"

    mock_faculty = MagicMock()
    mock_faculty.tenant_id = tenant_id
    mock_faculty.assigned_role = "Student"  # Invalid role for logging intervention

    service.tenant_repo.exists = AsyncMock(return_value=True)
    service.user_repo.get_by_id = AsyncMock(
        side_effect=lambda x: mock_student if x == student_id else mock_faculty
    )

    with pytest.raises(ValidationError) as exc:
        await service.create_intervention(
            tenant_id=tenant_id,
            student_user_id=student_id,
            faculty_user_id=faculty_id,
            intervention_notes="Notes",
        )
    assert exc.value.error_code == "invalid_faculty_role"

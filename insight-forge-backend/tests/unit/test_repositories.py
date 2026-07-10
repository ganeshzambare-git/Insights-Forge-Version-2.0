"""
Insight Forge V2 — Repository Unit Tests.

Validates repository class initialization, typing, session interaction, and query builders using mocks.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.models import (
    Tenant,
    User,
    Session,
    Cohort,
    StudentMetric,
    CoachingIntervention,
)
from app.repositories import (
    BaseRepository,
    TenantRepository,
    UserRepository,
    SessionRepository,
    CohortRepository,
    StudentMetricRepository,
    CoachingInterventionRepository,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    """Provide a mock AsyncSession with properly configured sync/async methods."""
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


def test_base_repository_init(mock_session: AsyncMock) -> None:
    """Verify BaseRepository initializes with a model and session."""
    repo = BaseRepository(model=Tenant, session=mock_session)
    assert repo.model == Tenant
    assert repo.session == mock_session


@pytest.mark.anyio
async def test_base_repository_create(mock_session: AsyncMock) -> None:
    """Verify BaseRepository.create adds entity to session."""
    repo = BaseRepository(model=Tenant, session=mock_session)
    tenant = Tenant(tenant_name="Test Tenant", tenant_slug="test-slug")

    result = await repo.create(tenant)
    assert result == tenant
    mock_session.add.assert_called_once_with(tenant)


@pytest.mark.anyio
async def test_tenant_repository_get_by_slug(mock_session: AsyncMock) -> None:
    """Verify TenantRepository.get_by_slug queries correctly."""
    repo = TenantRepository(session=mock_session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Tenant(tenant_slug="slug-a")
    mock_session.execute.return_value = mock_result

    result = await repo.get_by_slug("slug-a")
    assert result is not None
    assert result.tenant_slug == "slug-a"
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_user_repository_get_by_email(mock_session: AsyncMock) -> None:
    """Verify UserRepository.get_by_email queries correctly."""
    repo = UserRepository(session=mock_session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(corporate_email="user@test.com")
    mock_session.execute.return_value = mock_result

    result = await repo.get_by_email("user@test.com")
    assert result is not None
    assert result.corporate_email == "user@test.com"
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_session_repository_get_by_jti(mock_session: AsyncMock) -> None:
    """Verify SessionRepository.get_by_jti queries correctly."""
    repo = SessionRepository(session=mock_session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Session(jwt_jti="jti-token")
    mock_session.execute.return_value = mock_result

    result = await repo.get_by_jti("jti-token")
    assert result is not None
    assert result.jwt_jti == "jti-token"
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_cohort_repository_get_by_code(mock_session: AsyncMock) -> None:
    """Verify CohortRepository.get_by_code queries correctly."""
    repo = CohortRepository(session=mock_session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Cohort(cohort_code="c-101")
    mock_session.execute.return_value = mock_result

    tenant_id = uuid.uuid4()
    result = await repo.get_by_code(tenant_id, "c-101")
    assert result is not None
    assert result.cohort_code == "c-101"
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_student_metric_repository_get_by_student(
    mock_session: AsyncMock,
) -> None:
    """Verify StudentMetricRepository.get_by_student queries correctly."""
    repo = StudentMetricRepository(session=mock_session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [StudentMetric()]
    mock_session.execute.return_value = mock_result

    tenant_id = uuid.uuid4()
    student_id = uuid.uuid4()
    result = await repo.get_by_student(tenant_id, student_id)
    assert len(result) == 1
    mock_session.execute.assert_called_once()


@pytest.mark.anyio
async def test_coaching_intervention_repository_get_recent(
    mock_session: AsyncMock,
) -> None:
    """Verify CoachingInterventionRepository.get_recent_interventions queries correctly."""
    repo = CoachingInterventionRepository(session=mock_session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [CoachingIntervention()]
    mock_session.execute.return_value = mock_result

    tenant_id = uuid.uuid4()
    result = await repo.get_recent_interventions(tenant_id, limit=5)
    assert len(result) == 1
    mock_session.execute.assert_called_once()

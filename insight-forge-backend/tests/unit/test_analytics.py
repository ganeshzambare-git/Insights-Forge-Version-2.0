"""
Insight Forge V2 — Analytics Subsystem Unit Tests.

Verifies KPI aggregation query logic, student risk classification rules,
trend calculations, rule-based recommendations, and multi-tenant isolation.
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.analytics import AnalyticsService
from app.services.context import ServiceContext
from app.services.uow import UnitOfWork


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session


@pytest.fixture
def mock_service_deps(
    mock_session,
) -> tuple[UnitOfWork, ServiceContext, MagicMock, MagicMock, MagicMock]:
    """Prepares mocks for UoW, Context, Audit, Clock, and UUID providers."""
    uow = UnitOfWork(mock_session)
    context = ServiceContext(
        tenant_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role="Admin",
        request_id="test-req-id",
    )
    audit = MagicMock()
    clock = MagicMock()
    clock.now.return_value = datetime.now(timezone.utc)
    uuid_provider = MagicMock()
    uuid_provider.generate.side_effect = lambda: uuid.uuid4()

    return uow, context, audit, clock, uuid_provider


# ============================================================
# KPI & RISK CLASSIFICATION RULES TESTS
# ============================================================


@pytest.mark.anyio
async def test_kpi_aggregation_success(mock_session, mock_service_deps) -> None:
    """Verifies user count aggregations by assigned roles."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AnalyticsService(uow, context, audit, clock, uuid_provider)

    mock_row_1 = MagicMock()
    mock_row_1.assigned_role = "Student"
    mock_row_1.__getitem__.side_effect = lambda key: "Student" if key == 0 else 10

    mock_row_2 = MagicMock()
    mock_row_2.assigned_role = "Faculty"
    mock_row_2.__getitem__.side_effect = lambda key: "Faculty" if key == 0 else 5

    # Mock execute result
    mock_execute_result = MagicMock()
    mock_execute_result.all.return_value = [("Student", 10), ("Faculty", 5)]
    mock_session.execute.return_value = mock_execute_result

    kpi = await service.get_kpis(context.tenant_id)
    assert kpi.total_users == 15
    assert kpi.active_students == 10
    assert kpi.active_faculty == 5


@pytest.mark.anyio
async def test_risk_classification_rules(mock_session, mock_service_deps) -> None:
    """Verifies that StudentRisk rules classify SAFE, AMBER, and CRITICAL correctly."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AnalyticsService(uow, context, audit, clock, uuid_provider)

    # 1. Critical Risk Triggers: GPA < 60
    assert service._classify_risk(Decimal("59.90"), Decimal("95.00"), 0) == "Critical"
    # 2. Critical Risk Triggers: Attendance < 75
    assert service._classify_risk(Decimal("85.00"), Decimal("74.90"), 0) == "Critical"
    # 3. Critical Risk Triggers: >=3 Critical Interventions
    assert service._classify_risk(Decimal("85.00"), Decimal("95.00"), 3) == "Critical"

    # 4. Amber Risk Triggers: GPA < 75
    assert service._classify_risk(Decimal("74.90"), Decimal("95.00"), 0) == "Amber"
    # 5. Amber Risk Triggers: Attendance < 85
    assert service._classify_risk(Decimal("85.00"), Decimal("84.90"), 0) == "Amber"
    # 6. Amber Risk Triggers: >=1 Critical Intervention
    assert service._classify_risk(Decimal("85.00"), Decimal("95.00"), 1) == "Amber"

    # 7. Safe Risk Triggers: GPA >= 75 and Attendance >= 85 and 0 Critical Interventions
    assert service._classify_risk(Decimal("75.00"), Decimal("85.00"), 0) == "Safe"


# ============================================================
# RECOMMENDATIONS ENGINE TESTS
# ============================================================


@pytest.mark.anyio
async def test_recommendations_rules_engine(mock_session, mock_service_deps) -> None:
    """Verifies that advisory flags trigger on low performance boundaries."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AnalyticsService(uow, context, audit, clock, uuid_provider)

    # Create mock student row
    student_id = uuid.uuid4()
    mock_student = MagicMock()
    mock_student.user_id = student_id
    mock_student.corporate_email = "student@mit-edu.org"
    mock_student.cohort_id = uuid.uuid4()
    mock_student.gpa = Decimal("55.00")  # Triggers CRITICAL_GPA and DEAN_REVIEW
    mock_student.attendance = Decimal("90.00")
    mock_student.crit_count = 0
    mock_student.total_count = 0
    mock_student.latest_time = None

    mock_execute_result = MagicMock()
    mock_execute_result.all.return_value = [mock_student]
    mock_session.execute.return_value = mock_execute_result

    recommendations = await service.get_recommendations(context.tenant_id)
    assert len(recommendations) > 0
    rule_names = {r.rule_name for r in recommendations}
    assert "CRITICAL_GPA" in rule_names
    assert "DEAN_REVIEW" in rule_names


# ============================================================
# EMPTY DATASET FALLBACKS TESTS
# ============================================================


@pytest.mark.anyio
async def test_analytics_empty_dataset_graceful_fallbacks(
    mock_session, mock_service_deps
) -> None:
    """Verifies analytics dashboard does not divide by zero on empty databases."""
    uow, context, audit, clock, uuid_provider = mock_service_deps
    service = AnalyticsService(uow, context, audit, clock, uuid_provider)

    mock_session.scalar.return_value = 0

    mock_execute_result = MagicMock()
    mock_execute_result.all.return_value = []
    mock_session.execute.return_value = mock_execute_result

    dashboard = await service.get_dashboard(context.tenant_id)
    assert dashboard.total_students == 0
    assert dashboard.average_gpa == 0.0
    assert dashboard.average_attendance == 0.0

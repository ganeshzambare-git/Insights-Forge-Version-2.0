"""
Insight Forge V2 — REST API Endpoints Integration & Unit Tests.

Uses FastAPI TestClient and dependency overrides to verify REST controllers,
schemas validation, custom status codes, and standard envelope mappings offline.
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_user
from app.dependencies.services import (
    get_tenant_service,
    get_user_service,
    get_cohort_service,
    get_student_metric_service,
    get_coaching_intervention_service,
)
from app.models.user import User
from app.models.tenant import Tenant
from app.models.cohort import Cohort
from app.models.student_metric import StudentMetric
from app.models.coaching_intervention import CoachingIntervention
from app.services.result import ServiceResult


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Clear dependency overrides after each test to prevent leaking state."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_client() -> TestClient:
    """Prepares FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def mock_tenant() -> Tenant:
    """Provides a sample Tenant model instance."""
    return Tenant(
        tenant_id=uuid.uuid4(),
        tenant_slug="mit-university",
        tenant_name="MIT University",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user(mock_tenant) -> User:
    """Provides a sample User model instance."""
    return User(
        user_id=uuid.uuid4(),
        tenant_id=mock_tenant.tenant_id,
        corporate_email="admin@college.edu",
        password_hash="fake-hash",
        assigned_role="Admin",
        is_mfa_enabled=True,
    )


# ============================================================
# TENANTS ENDPOINTS TESTS
# ============================================================


@pytest.mark.anyio
async def test_tenant_create_success(test_client, mock_user, mock_tenant) -> None:
    """Verifies POST /api/v1/tenants returns 201 and matches response envelope."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    tenant_service = MagicMock()
    tenant_service.create_tenant = AsyncMock(
        return_value=ServiceResult(
            success=True, data=mock_tenant, message="Tenant created."
        )
    )
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service

    payload = {"tenant_slug": "mit-university", "tenant_name": "MIT University"}
    response = test_client.post("/api/v1/tenants", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["tenant_name"] == "MIT University"
    assert "request_id" in json_data["meta"]


@pytest.mark.anyio
async def test_tenant_get_by_id(test_client, mock_user, mock_tenant) -> None:
    """Verifies GET /api/v1/tenants/{id} retrieves the correct tenant."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    tenant_service = MagicMock()
    tenant_service.get_tenant = AsyncMock(return_value=mock_tenant)
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service

    url = f"/api/v1/tenants/{mock_tenant.tenant_id}"
    response = test_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["tenant_slug"] == "mit-university"


@pytest.mark.anyio
async def test_tenant_patch_success(test_client, mock_user, mock_tenant) -> None:
    """Verifies PATCH /api/v1/tenants/{id} successfully updates tenant details."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    tenant_service = MagicMock()
    tenant_service.update_tenant = AsyncMock(
        return_value=ServiceResult(
            success=True, data=mock_tenant, message="Tenant updated."
        )
    )
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service

    url = f"/api/v1/tenants/{mock_tenant.tenant_id}"
    payload = {"tenant_name": "MIT University East"}
    response = test_client.patch(url, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


@pytest.mark.anyio
async def test_tenant_delete_success(test_client, mock_user, mock_tenant) -> None:
    """Verifies DELETE /api/v1/tenants/{id} deletes tenant returning 204."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    tenant_service = MagicMock()
    tenant_service.delete_tenant = AsyncMock(
        return_value=ServiceResult(success=True, data=None, message="Deleted.")
    )
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service

    url = f"/api/v1/tenants/{mock_tenant.tenant_id}"
    response = test_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================
# USERS ENDPOINTS TESTS
# ============================================================


@pytest.mark.anyio
async def test_user_create_success(test_client, mock_user, mock_tenant) -> None:
    """Verifies POST /api/v1/users registers a new user under proper role."""
    mock_user.assigned_role = "Dean"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    user_service = MagicMock()
    created_user = User(
        user_id=uuid.uuid4(),
        tenant_id=mock_tenant.tenant_id,
        corporate_email="faculty@college.edu",
        password_hash="hashed-pw",
        assigned_role="Faculty",
        is_mfa_enabled=True,
    )
    user_service.create_user = AsyncMock(
        return_value=ServiceResult(
            success=True, data=created_user, message="User created."
        )
    )
    app.dependency_overrides[get_user_service] = lambda: user_service

    payload = {
        "corporate_email": "faculty@college.edu",
        "password": "StrongPass123!",
        "assigned_role": "Faculty",
    }
    response = test_client.post("/api/v1/users", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["data"]["assigned_role"] == "Faculty"


@pytest.mark.anyio
async def test_user_validation_failure(test_client, mock_user) -> None:
    """Verifies invalid user payloads return 422 Unprocessable Entity."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "corporate_email": "not-an-email",
        "password": "short",
        "assigned_role": "InvalidRole",
    }
    response = test_client.post("/api/v1/users", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ============================================================
# COHORTS ENDPOINTS TESTS
# ============================================================


@pytest.mark.anyio
async def test_cohort_create_success(test_client, mock_user, mock_tenant) -> None:
    """Verifies cohort creation log."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    cohort_service = MagicMock()
    mock_cohort = Cohort(
        cohort_id=uuid.uuid4(),
        tenant_id=mock_tenant.tenant_id,
        cohort_code="CS-2026",
        department_scope="Computer Science",
    )
    cohort_service.create_cohort = AsyncMock(
        return_value=ServiceResult(
            success=True, data=mock_cohort, message="Cohort created."
        )
    )
    app.dependency_overrides[get_cohort_service] = lambda: cohort_service

    payload = {"cohort_code": "CS-2026", "department_scope": "Computer Science"}
    response = test_client.post("/api/v1/cohorts", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["data"]["cohort_code"] == "CS-2026"


# ============================================================
# METRICS ENDPOINTS TESTS
# ============================================================


@pytest.mark.anyio
async def test_student_metric_create_success(
    test_client, mock_user, mock_tenant
) -> None:
    """Verifies academic performance metric logging."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    metric_service = MagicMock()
    mock_metric = StudentMetric(
        metric_id=101,
        tenant_id=mock_tenant.tenant_id,
        student_user_id=uuid.uuid4(),
        cohort_id=uuid.uuid4(),
        raw_average_grade=Decimal("85.50"),
        normalized_grade_score=None,
        attendance_percentage=Decimal("92.00"),
        success_indicator_status="Safe",
        reporting_period="2025-2026",
    )
    metric_service.add_metric = AsyncMock(
        return_value=ServiceResult(
            success=True, data=mock_metric, message="Logged metric."
        )
    )
    app.dependency_overrides[get_student_metric_service] = lambda: metric_service

    payload = {
        "student_id": str(mock_metric.student_user_id),
        "cohort_id": str(mock_metric.cohort_id),
        "academic_year": "2025-2026",
        "gpa": 85.50,
        "attendance_rate": 92.00,
        "status_indicator": "Safe",
    }
    response = test_client.post("/api/v1/metrics", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["data"]["metric_id"] == 101


# ============================================================
# COACHING INTERVENTIONS ENDPOINTS TESTS
# ============================================================


@pytest.mark.anyio
async def test_intervention_create_success(test_client, mock_user, mock_tenant) -> None:
    """Verifies coaching intervention session logging."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    intervention_service = MagicMock()
    mock_intervention = CoachingIntervention(
        intervention_id=uuid.uuid4(),
        tenant_id=mock_tenant.tenant_id,
        student_user_id=uuid.uuid4(),
        faculty_user_id=mock_user.user_id,
        intervention_notes="Academic consultation notes.",
        recorded_timestamp=datetime.now(timezone.utc),
    )
    intervention_service.create_intervention = AsyncMock(
        return_value=ServiceResult(
            success=True, data=mock_intervention, message="Logged intervention."
        )
    )
    app.dependency_overrides[get_coaching_intervention_service] = (
        lambda: intervention_service
    )

    payload = {
        "student_id": str(mock_intervention.student_user_id),
        "advisor_id": str(mock_intervention.faculty_user_id),
        "intervention_notes": "Academic consultation notes.",
    }
    response = test_client.post("/api/v1/interventions", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["data"]["intervention_notes"] == "Academic consultation notes."
    )


# ============================================================
# RBAC SECURITY GATES TESTS
# ============================================================


@pytest.mark.anyio
async def test_rbac_unauthorized_role(test_client, mock_user) -> None:
    """Verifies role restriction (e.g. Student accessing Admin Tenant endpoint)."""
    mock_user.assigned_role = "Student"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/tenants")

    # Access is forbidden for Student role
    assert response.status_code == status.HTTP_403_FORBIDDEN

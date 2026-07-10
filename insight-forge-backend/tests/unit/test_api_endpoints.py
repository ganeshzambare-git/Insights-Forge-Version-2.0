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


@pytest.mark.anyio
async def test_tenant_verify_slug_success(test_client, mock_tenant) -> None:
    """Verifies public GET /api/v1/tenants/verify/{slug} returns tenant data without auth."""
    tenant_service = MagicMock()
    tenant_service.get_tenant_by_slug = AsyncMock(return_value=mock_tenant)
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service

    url = f"/api/v1/tenants/verify/{mock_tenant.tenant_slug}"
    response = test_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["tenant_slug"] == "mit-university"
    assert "request_id" in json_data["meta"]


@pytest.mark.anyio
async def test_tenant_verify_slug_not_found(test_client) -> None:
    """Verifies public GET /api/v1/tenants/verify/{slug} returns 404 on invalid slug."""
    tenant_service = MagicMock()
    tenant_service.get_tenant_by_slug = AsyncMock(return_value=None)
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service

    url = "/api/v1/tenants/verify/nonexistent-slug"
    response = test_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["errors"][0]["error"] == "tenant_not_found"
    assert "not found" in json_data["errors"][0]["message"].lower()


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

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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


@pytest.mark.anyio
async def test_admin_cluster_metrics_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/admin/cluster-metrics succeeds for Admin."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/admin/cluster-metrics")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "server_health" in json_data["data"]
    assert "pyspark_load" in json_data["data"]
    assert "inbound_traffic" in json_data["data"]


@pytest.mark.anyio
async def test_admin_cluster_metrics_forbidden(test_client, mock_user) -> None:
    """Verifies GET /api/v1/admin/cluster-metrics fails for non-Admin (e.g., Faculty)."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/admin/cluster-metrics")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_admin_rotate_keys_authorized(test_client, mock_user) -> None:
    """Verifies POST /api/v1/admin/rotate-keys succeeds for Admin."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.post("/api/v1/admin/rotate-keys")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "rotated_at" in json_data["data"]


@pytest.mark.anyio
async def test_admin_rate_limit_logs_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/admin/rate-limit-logs succeeds for Admin."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/admin/rate-limit-logs")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "logs" in json_data["data"]
    assert "threshold_limit" in json_data["data"]


@pytest.mark.anyio
async def test_ingest_upload_telemetry_authorized(test_client, mock_user) -> None:
    """Verifies POST /api/v1/ingest/upload-telemetry succeeds for Admin."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "file_id": "test-transaction-uuid",
        "chunk_index": 0,
        "total_chunks": 5
    }
    files = {
        "file": ("test_chunk.csv", b"col1,col2\nval1,val2", "text/csv")
    }

    response = test_client.post("/api/v1/ingest/upload-telemetry", data=payload, files=files)

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["chunk_index"] == 0
    assert json_data["data"]["status"] == "Processing"


@pytest.mark.anyio
async def test_analytics_executive_summary_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/analytics/executive-summary succeeds for Dean."""
    mock_user.assigned_role = "Dean"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/analytics/executive-summary")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "kpis" in json_data["data"]
    assert "departments" in json_data["data"]


@pytest.mark.anyio
async def test_analytics_department_records_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/analytics/department-records succeeds for Faculty."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/analytics/department-records?scope=Sciences")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["scope"] == "Sciences"
    assert "records" in json_data["data"]


@pytest.mark.anyio
async def test_simulation_project_curves_authorized(test_client, mock_user) -> None:
    """Verifies POST /api/v1/simulations/project-curves succeeds for Dean."""
    mock_user.assigned_role = "Dean"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "credit_ratio": 0.85,
        "target_cohorts": 15,
        "class_capacity": 45
    }
    response = test_client.post("/api/v1/simulations/project-curves", json=payload)

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "success_rate" in json_data["data"]
    assert "average_gpa" in json_data["data"]


@pytest.mark.anyio
async def test_analytics_export_audit_packet_authorized(test_client, mock_user) -> None:
    """Verifies POST /api/v1/analytics/export-audit-packet succeeds for Dean."""
    mock_user.assigned_role = "Dean"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.post("/api/v1/analytics/export-audit-packet")

    assert response.status_code == status.HTTP_202_ACCEPTED
    json_data = response.json()
    assert json_data["success"] is True
    assert "job_id" in json_data["data"]
    assert json_data["data"]["status"] == "Processing"


@pytest.mark.anyio
async def test_cohort_roster_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/cohorts/{cohort_id}/roster succeeds for Faculty."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user
    cohort_uuid = uuid.uuid4()

    response = test_client.get(f"/api/v1/cohorts/{cohort_uuid}/roster")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "records" in json_data["data"]
    assert json_data["data"]["total_count"] == 200


@pytest.mark.anyio
async def test_cohort_roster_search_filter(test_client, mock_user) -> None:
    """Verifies GET /api/v1/cohorts/{cohort_id}/roster filters results by search query."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user
    cohort_uuid = uuid.uuid4()

    # Search query "john"
    response = test_client.get(f"/api/v1/cohorts/{cohort_uuid}/roster?search=john")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    for item in json_data["data"]["records"]:
        assert "john" in item["name"].lower() or "john" in item["email"].lower()


@pytest.mark.anyio
async def test_record_coaching_intervention_authorized(test_client, mock_user) -> None:
    """Verifies POST /api/v1/interventions/record succeeds for Faculty."""
    mock_user.assigned_role = "Faculty"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    from app.services.result import ServiceResult
    from unittest.mock import AsyncMock
    from app.models.coaching_intervention import CoachingIntervention

    # Mock the coaching intervention database object
    mock_intervention = CoachingIntervention(
        intervention_id=uuid.uuid4(),
        tenant_id=mock_user.tenant_id,
        student_user_id=uuid.uuid4(),
        faculty_user_id=mock_user.user_id,
        intervention_notes="Discussed academic study plans and tutoring options.",
        recorded_timestamp=datetime.now(timezone.utc),
    )

    intervention_service = AsyncMock()
    intervention_service.create_intervention = AsyncMock(
        return_value=ServiceResult(
            success=True, data=mock_intervention, message="Logged intervention."
        )
    )
    app.dependency_overrides[get_coaching_intervention_service] = lambda: intervention_service

    payload = {
        "tenant_id": "tenant-001",
        "student_user_id": str(mock_intervention.student_user_id),
        "intervention_notes": "Discussed academic study plans and tutoring options."
    }
    response = test_client.post("/api/v1/interventions/record", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["message"] == "Academic intervention action recorded securely."
    assert "intervention_id" in json_data["data"]


@pytest.mark.anyio
async def test_student_progress_summary_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/student/progress-summary succeeds for Student role."""
    mock_user.assigned_role = "Student"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/student/progress-summary?term=Fall%202026")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["gpa"] == 3.65
    assert json_data["data"]["attendance_rate"] == 96


@pytest.mark.anyio
async def test_student_normalized_grades_authorized(test_client, mock_user) -> None:
    """Verifies GET /api/v1/student/normalized-grades succeeds for Student role."""
    mock_user.assigned_role = "Student"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/student/normalized-grades?term=Spring%202026")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "student_gpa_history" in json_data["data"]
    assert "cohort_gpa_history" in json_data["data"]


@pytest.mark.anyio
async def test_get_dead_letter_logs(test_client, mock_user) -> None:
    """Verifies GET /api/v1/ingest/dead-letter-logs returns malformed logs."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/ingest/dead-letter-logs")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]["logs"]) == 2
    assert json_data["data"]["logs"][0]["payload_id"] == "err-90921"


@pytest.mark.anyio
async def test_delete_cohort_conflict(test_client, mock_user) -> None:
    """Verifies DELETE /api/v1/cohorts/{id} raises HTTP 409 Conflict with dependencies list."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.delete("/api/v1/cohorts/88888888-8888-8888-8888-888888888888")

    assert response.status_code == status.HTTP_409_CONFLICT
    json_data = response.json()
    assert json_data["success"] is False
    assert "underlying operational records remain active" in json_data["message"]
    assert len(json_data["data"]["dependencies"]) == 2


# ============================================================
# PHASE 7 – Tasks 25, 26, 27 Endpoint Tests
# ============================================================


@pytest.mark.anyio
async def test_get_attendance_summary(test_client, mock_user) -> None:
    """Verifies GET /api/v1/analytics/attendance/summary returns trend data and KPI summary."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/analytics/attendance/summary")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "trend" in json_data["data"]
    assert "summary" in json_data["data"]
    assert len(json_data["data"]["trend"]) == 12
    assert json_data["data"]["summary"]["total_months"] == 12
    assert json_data["data"]["summary"]["average_attendance_rate"] > 0


@pytest.mark.anyio
async def test_get_attendance_summary_with_semester_filter(test_client, mock_user) -> None:
    """Verifies attendance summary respects semester query filter."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/analytics/attendance/summary?semester=Spring+2026")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    trend = json_data["data"]["trend"]
    assert all(t["semester"] == "Spring 2026" for t in trend)
    assert json_data["data"]["summary"]["total_months"] == 6


@pytest.mark.anyio
async def test_get_course_evaluation(test_client, mock_user) -> None:
    """Verifies GET /api/v1/analytics/courses/evaluation returns course metrics."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/analytics/courses/evaluation")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "courses" in json_data["data"]
    assert json_data["data"]["total_courses"] == 4
    course = json_data["data"]["courses"][0]
    assert "course_id" in course
    assert "avg_score" in course
    assert "kpi_status" in course


@pytest.mark.anyio
async def test_get_course_evaluation_with_department_filter(test_client, mock_user) -> None:
    """Verifies course evaluation respects department query filter."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/analytics/courses/evaluation?department=Computer+Science")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    courses = json_data["data"]["courses"]
    assert all(c["department"] == "Computer Science" for c in courses)
    assert json_data["data"]["total_courses"] == 2


@pytest.mark.anyio
async def test_get_resource_allocation(test_client, mock_user) -> None:
    """Verifies GET /api/v1/finance/resource-allocation returns budget ledger and utilization."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/finance/resource-allocation")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "budget_ledger" in json_data["data"]
    assert "utilization_cards" in json_data["data"]
    assert "financial_summary" in json_data["data"]
    assert len(json_data["data"]["budget_ledger"]) == 4
    assert len(json_data["data"]["utilization_cards"]) == 4
    summary = json_data["data"]["financial_summary"]
    assert summary["total_allocated"] > 0
    assert summary["overall_utilization_pct"] > 0


@pytest.mark.anyio
async def test_get_resource_allocation_with_dimension_filter(test_client, mock_user) -> None:
    """Verifies resource allocation respects dimension query filter."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/finance/resource-allocation?dimension=Technology")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    ledger = json_data["data"]["budget_ledger"]
    assert all(b["dimension"] == "Technology" for b in ledger)
    assert len(ledger) == 1


# ============================================================
# PHASE 8 – Tasks 28, 29 Endpoint Tests
# ============================================================


@pytest.mark.anyio
async def test_get_task_status_running(test_client, mock_user) -> None:
    """Verifies GET /api/v1/tasks/status/{task_id} returns Running task state."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/tasks/status/task-running-001")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "Running"
    assert json_data["data"]["progress_pct"] == 62
    assert json_data["data"]["task_type"] == "ML_RISK_PIPELINE"
    assert len(json_data["data"]["timeline"]) == 3


@pytest.mark.anyio
async def test_get_task_status_completed(test_client, mock_user) -> None:
    """Verifies GET /api/v1/tasks/status/{task_id} returns Completed task with result."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/tasks/status/task-completed-002")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "Completed"
    assert json_data["data"]["progress_pct"] == 100
    assert json_data["data"]["result"] is not None
    assert json_data["data"]["result"]["record_count"] == 1840


@pytest.mark.anyio
async def test_get_task_status_failed(test_client, mock_user) -> None:
    """Verifies GET /api/v1/tasks/status/{task_id} returns Failed task with error details."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/tasks/status/task-failed-003")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "Failed"
    assert json_data["data"]["error"] is not None
    assert json_data["data"]["error"]["code"] == "CSV_SCHEMA_MISMATCH"
    assert "recovery" in json_data["data"]["error"]


@pytest.mark.anyio
async def test_get_task_status_pending_unknown(test_client, mock_user) -> None:
    """Verifies unknown task_id returns Pending state gracefully."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/tasks/status/task-unknown-999")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "Pending"
    assert json_data["data"]["progress_pct"] == 0


@pytest.mark.anyio
async def test_list_tasks(test_client, mock_user) -> None:
    """Verifies GET /api/v1/tasks/list returns all task summaries."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/tasks/list")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["total"] == 3
    assert len(json_data["data"]["tasks"]) == 3


@pytest.mark.anyio
async def test_get_security_audit_logs(test_client, mock_user) -> None:
    """Verifies GET /api/v1/admin/security-audit-logs returns all audit records."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/admin/security-audit-logs")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    assert "logs" in json_data["data"]
    assert json_data["data"]["total_records"] == 6
    log = json_data["data"]["logs"][0]
    assert "audit_id" in log
    assert "event_type" in log
    assert "severity" in log
    assert "source_ip" in log
    assert "metadata" in log


@pytest.mark.anyio
async def test_get_security_audit_logs_severity_filter(test_client, mock_user) -> None:
    """Verifies security audit logs respect severity query filter."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/admin/security-audit-logs?severity=CRITICAL")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    logs = json_data["data"]["logs"]
    assert all(l["severity"] == "CRITICAL" for l in logs)
    assert json_data["data"]["total_records"] == 2


@pytest.mark.anyio
async def test_get_security_audit_logs_event_type_filter(test_client, mock_user) -> None:
    """Verifies security audit logs respect event_type query filter."""
    mock_user.assigned_role = "Admin"
    app.dependency_overrides[get_current_user] = lambda: mock_user

    response = test_client.get("/api/v1/admin/security-audit-logs?event_type=LOGIN_FAILED")

    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert json_data["success"] is True
    logs = json_data["data"]["logs"]
    assert len(logs) == 1
    assert logs[0]["event_type"] == "LOGIN_FAILED"


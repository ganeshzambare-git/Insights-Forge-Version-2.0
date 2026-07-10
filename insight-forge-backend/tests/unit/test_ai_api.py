"""
Insight Forge V2 — REST API Endpoints Integration and Unit Tests for AI Controller.

Verifies the POST /api/v1/ai/analyze endpoint, authentication requirements,
role validation (RBAC), error handling, and output schemas offline.
"""

from datetime import datetime, timezone
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from app.core.roles import Role


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
        tenant_slug="oxford-university",
        tenant_name="Oxford University",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user(mock_tenant) -> User:
    """Provides a sample User model instance with Admin role."""
    return User(
        user_id=uuid.uuid4(),
        tenant_id=mock_tenant.tenant_id,
        corporate_email="admin@oxford.edu",
        password_hash="fake-hash",
        assigned_role=Role.ADMIN.value,
        is_mfa_enabled=True,
    )


@pytest.mark.anyio
async def test_ai_analyze_endpoint_success(test_client, mock_user) -> None:
    """Verifies POST /api/v1/ai/analyze returns 200 and maps execution metrics and reports."""
    mock_user.assigned_role = Role.FACULTY.value  # allowed role
    app.dependency_overrides[get_current_user] = lambda: mock_user

    csv_content = (
        b"student_id,grade\n"
        b"S001,85\n"
        b"S002,92\n"
        b"S003,78\n"
        b"S004,95\n"
        b"S005,80\n"
    )
    files = {"file": ("student_grades.csv", csv_content, "text/csv")}

    response = test_client.post("/api/v1/ai/analyze", files=files)
    assert response.status_code == status.HTTP_200_OK

    json_data = response.json()
    if not json_data.get("success"):
        print(f"\n--- DEBUG: {json_data} ---")
    assert json_data["success"] is True
    assert "data" in json_data
    assert "metrics" in json_data["data"]
    assert "consolidated_report" in json_data["data"]

    # Verify that the report includes executive summaries and scores
    report = json_data["data"]["consolidated_report"]
    assert "executive_summary" in report
    assert "business_health_score" in report
    assert "key_findings" in report
    assert "strategic_recommendations" in report


@pytest.mark.anyio
async def test_ai_analyze_endpoint_unauthorized(test_client) -> None:
    """Verifies POST /api/v1/ai/analyze returns 401 Unauthorized when no credentials are provided."""
    csv_content = b"student_id,grade\nS001,85\n"
    files = {"file": ("student_grades.csv", csv_content, "text/csv")}

    # Send request without overriding get_current_user or sending tokens
    response = test_client.post("/api/v1/ai/analyze", files=files)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_ai_analyze_endpoint_forbidden_role(test_client, mock_user) -> None:
    """Verifies POST /api/v1/ai/analyze returns 403 Forbidden for Student role."""
    mock_user.assigned_role = Role.STUDENT.value  # unauthorized role
    app.dependency_overrides[get_current_user] = lambda: mock_user

    csv_content = b"student_id,grade\nS001,85\n"
    files = {"file": ("student_grades.csv", csv_content, "text/csv")}

    response = test_client.post("/api/v1/ai/analyze", files=files)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_ai_analyze_endpoint_empty_dataset(test_client, mock_user) -> None:
    """Verifies POST /api/v1/ai/analyze handles empty datasets by returning warning metrics."""
    mock_user.assigned_role = Role.ADMIN.value
    app.dependency_overrides[get_current_user] = lambda: mock_user

    csv_content = b""  # Empty content
    files = {"file": ("empty.csv", csv_content, "text/csv")}

    response = test_client.post("/api/v1/ai/analyze", files=files)
    assert response.status_code == status.HTTP_200_OK

    json_data = response.json()
    assert json_data["success"] is False
    assert "Empty dataset uploaded" in json_data["data"]["warnings"][0]

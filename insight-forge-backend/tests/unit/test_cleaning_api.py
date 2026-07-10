"""
Insight Forge V2 — REST API Endpoints Integration and Unit Tests for Cleaning Controller.

Verifies the POST /api/v1/cleaning/analyze endpoint, authentication requirements,
role validation (RBAC), file parsing, quality checks, and output schemas.
"""

from datetime import datetime, timezone
from typing import Any
import io
import zipfile
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
        tenant_slug="stanford-university",
        tenant_name="Stanford University",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user(mock_tenant) -> User:
    """Provides a sample User model instance with Faculty role."""
    return User(
        user_id=uuid.uuid4(),
        tenant_id=mock_tenant.tenant_id,
        corporate_email="faculty@stanford.edu",
        password_hash="fake-hash",
        assigned_role=Role.FACULTY.value,
        is_mfa_enabled=False,
    )


def create_mock_xlsx_bytes(rows: list[dict[str, Any]]) -> bytes:
    """Helper function to build a minimal in-memory XLSX file structure for testing."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        shared_strings = []
        string_to_idx = {}

        def get_string_idx(s: str) -> int:
            if s not in string_to_idx:
                string_to_idx[s] = len(shared_strings)
                shared_strings.append(s)
            return string_to_idx[s]

        if not rows:
            columns = []
        else:
            columns = list(rows[0].keys())

        # Build sheet1.xml row structure
        grid = []
        header_row_cells = []
        for col_idx, col_name in enumerate(columns):
            col_letter = chr(65 + col_idx)
            ref = f"{col_letter}1"
            str_idx = get_string_idx(col_name)
            header_row_cells.append(f'<c r="{ref}" t="s"><v>{str_idx}</v></c>')
        grid.append(f'<row r="1">{"".join(header_row_cells)}</row>')

        for row_idx, r_data in enumerate(rows):
            real_row_num = row_idx + 2
            row_cells = []
            for col_idx, col_name in enumerate(columns):
                col_letter = chr(65 + col_idx)
                ref = f"{col_letter}{real_row_num}"
                val = r_data[col_name]
                if val is None or val == "":
                    continue
                elif isinstance(val, (int, float)) and not isinstance(val, bool):
                    row_cells.append(f'<c r="{ref}"><v>{val}</v></c>')
                elif isinstance(val, bool):
                    row_cells.append(f'<c r="{ref}" t="b"><v>{"1" if val else "0"}</v></c>')
                else:
                    str_idx = get_string_idx(str(val))
                    row_cells.append(f'<c r="{ref}" t="s"><v>{str_idx}</v></c>')
            grid.append(f'<row r="{real_row_num}">{"".join(row_cells)}</row>')

        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n'
            '<sheetData>\n'
            f'{"".join(grid)}\n'
            '</sheetData>\n'
            '</worksheet>'
        )
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)

        ss_items = []
        for s in shared_strings:
            ss_items.append(f'<si><t>{s}</t></si>')
        ss_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{0}" uniqueCount="{0}">\n'
            '{1}\n'
            '</sst>'
        ).format(len(shared_strings), "".join(ss_items))
        z.writestr("xl/sharedStrings.xml", ss_xml)
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"></workbook>')

    return out.getvalue()


@pytest.mark.anyio
async def test_cleaning_csv_upload_success(test_client, mock_user) -> None:
    """Verifies POST /api/v1/cleaning/analyze with a dirty CSV dataset detects all issues."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    csv_content = (
        b"OrderID,Email,Qty,Phone,DateColumn\n"
        b"O-100,alice@bob.com,10,1234567890,2026-07-09\n"
        b"O-100,alice@bob.com,10,1234567890,2026-07-09\n"  # Duplicate row
        b"O-102,bad_email_format,-5,invalid-phone,07/09/2026\n"  # Invalid email/phone, negative bound, mixed date formatting
        b"  O-103  ,test@domain.com,20,1234567890,2026-07-09\n"  # Whitespace issue
        b"O-104,ACTIVE@DOMAIN.COM,30,1234567890,2026-07-09\n"  # Category casing variation
        b"O-105,active@domain.com,40,1234567890,2026-07-09\n"
    )
    files = {"file": ("dirty_data.csv", csv_content, "text/csv")}

    response = test_client.post("/api/v1/cleaning/analyze", files=files)
    assert response.status_code == status.HTTP_200_OK

    json_data = response.json()
    assert json_data["success"] is True
    assert "summary" in json_data["data"]
    assert "cleaning_log" in json_data["data"]

    summary = json_data["data"]["summary"]
    assert summary["total_issues_detected"] > 0
    assert summary["overall_quality_score"] < 1.0
    assert summary["certification_status"] in ["Requires Review", "Not Certified"]

    recs = [r["issue_type"] for r in summary["cleaning_recommendations"]]
    assert "DUPLICATE_ROWS" in recs
    assert "DUPLICATE_IDENTIFIERS" in recs
    assert "WHITESPACE_ISSUES" in recs
    assert "INVALID_EMAIL_FORMAT" in recs
    assert "OUT_OF_RANGE_VALUES" in recs
    assert "CASING_INCONSISTENCY" in recs
    assert "MIXED_FORMATTING" in recs


@pytest.mark.anyio
async def test_cleaning_xlsx_upload_success(test_client, mock_user) -> None:
    """Verifies POST /api/v1/cleaning/analyze with an XLSX dataset parses correctly."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    rows = [
        {"OrderID": "O-100", "Email": "alice@bob.com", "Qty": 10},
        {"OrderID": "O-100", "Email": "alice@bob.com", "Qty": 10},  # Duplicate row
        {"OrderID": "O-102", "Email": "bad_email_format", "Qty": -5},
    ]
    xlsx_content = create_mock_xlsx_bytes(rows)
    files = {"file": ("dirty_data.xlsx", xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    response = test_client.post("/api/v1/cleaning/analyze", files=files)
    assert response.status_code == status.HTTP_200_OK

    json_data = response.json()
    assert json_data["success"] is True
    summary = json_data["data"]["summary"]
    recs = [r["issue_type"] for r in summary["cleaning_recommendations"]]
    assert "DUPLICATE_ROWS" in recs
    assert "DUPLICATE_IDENTIFIERS" in recs


@pytest.mark.anyio
async def test_cleaning_empty_dataset(test_client, mock_user) -> None:
    """Verifies POST /api/v1/cleaning/analyze handles empty files gracefully."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    files = {"file": ("empty.csv", b"", "text/csv")}
    response = test_client.post("/api/v1/cleaning/analyze", files=files)
    assert response.status_code == status.HTTP_200_OK

    json_data = response.json()
    assert json_data["success"] is True
    summary = json_data["data"]["summary"]
    assert summary["certification_status"] == "Not Certified"
    assert "Dataset is empty" in summary["warnings"][0]


@pytest.mark.anyio
async def test_cleaning_invalid_format(test_client, mock_user) -> None:
    """Verifies POST /api/v1/cleaning/analyze returns 422 validation error for unsupported format."""
    app.dependency_overrides[get_current_user] = lambda: mock_user

    files = {"file": ("image.png", b"fake-png-content", "image/png")}
    response = test_client.post("/api/v1/cleaning/analyze", files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    json_data = response.json()
    assert json_data["success"] is False
    assert "Unsupported file format" in json_data["errors"][0]["message"]



@pytest.mark.anyio
async def test_cleaning_authorization_failures(test_client, mock_user) -> None:
    """Verifies POST /api/v1/cleaning/analyze enforces role guards (RBAC)."""
    # Override user to Student role which is unauthorized
    mock_user.assigned_role = Role.STUDENT.value
    app.dependency_overrides[get_current_user] = lambda: mock_user

    files = {"file": ("data.csv", b"student_id,grade\nS001,85\n", "text/csv")}
    response = test_client.post("/api/v1/cleaning/analyze", files=files)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_cleaning_unauthenticated_failure(test_client) -> None:
    """Verifies POST /api/v1/cleaning/analyze returns 401 Unauthorized for unauthenticated requests."""
    files = {"file": ("data.csv", b"student_id,grade\nS001,85\n", "text/csv")}
    response = test_client.post("/api/v1/cleaning/analyze", files=files)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

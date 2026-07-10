"""
Insight Forge V2 — Data Cleaning Verification Script.

Tests FastAPI app startup, JWT login, and in-process execution of /api/v1/cleaning/analyze.
"""

import asyncio
import sys
from httpx import AsyncClient, ASGITransport

# Set selector event loop on Windows to support psycopg async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app


async def run_cleaning_verification() -> None:
    """Simulate user login and request execution against the cleaning endpoint."""
    print("=============================================================")
    print("INSIGHT FORGE V2.2 — DATA CLEANING VERIFICATION SYSTEM")
    print("=============================================================")

    # Use ASGI Transport to run the app in-process
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Authenticate to obtain the JWT token
        print("\n[1/4] Authenticating as Admin...")
        login_data = {
            "corporate_email": "admin@insightforge.com",
            "password": "AdminSecurePassword123!",
            "remember_me": False,
        }
        res = await client.post("/api/v1/auth/login", json=login_data)
        if res.status_code != 200:
            print(f"Error: Authentication failed: {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)

        res_json = res.json()
        token_data = res_json.get("data", {})
        access_token = token_data.get("access_token")
        if not access_token:
            print("Error: access_token not found in response payload.", file=sys.stderr)
            sys.exit(1)
        print("Successfully obtained JWT access token.")

        # 2. Test Cleaning Endpoint with Valid CSV
        print("\n[2/4] Uploading dirty CSV dataset to /api/v1/cleaning/analyze...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        csv_content = (
            b"OrderID,Email,Qty,Phone,DateColumn\n"
            b"O-100,alice@bob.com,10,1234567890,2026-07-09\n"
            b"O-100,alice@bob.com,10,1234567890,2026-07-09\n"  # Duplicate row
            b"O-102,bad_email_format,-5,invalid-phone,07/09/2026\n"  # Issues
            b"  O-103  ,test@domain.com,20,1234567890,2026-07-09\n"  # Whitespace
            b"O-104,ACTIVE@DOMAIN.COM,30,1234567890,2026-07-09\n"  # Casing
        )
        files = {"file": ("dirty_data.csv", csv_content, "text/csv")}
        
        res = await client.post("/api/v1/cleaning/analyze", headers=headers, files=files)
        if res.status_code != 200:
            print(f"Error: Cleaning analysis failed: {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)
            
        res_json = res.json()
        print("Response success:", res_json["success"])
        print("Response message:", res_json["message"])
        print("Quality Score:", res_json["data"]["summary"]["overall_quality_score"])
        print("Certification Tier:", res_json["data"]["summary"]["certification_status"])
        print("Total Issues:", res_json["data"]["summary"]["total_issues_detected"])
        print("Cleaning recommendations list:")
        for r in res_json["data"]["summary"]["cleaning_recommendations"]:
            print(f"  - Issue: {r['issue_type']} in columns {r['affected_columns']} | Severity: {r['severity']} -> Action: {r['recommended_action']}")

        # 3. Test Unsupported Format Validation (PNG Upload)
        print("\n[3/4] Uploading unsupported PNG file format (expecting 422)...")
        files = {"file": ("unsupported_image.png", b"fake-png-data", "image/png")}
        res = await client.post("/api/v1/cleaning/analyze", headers=headers, files=files)
        if res.status_code != 422:
            print(f"Error: Expected 422 Unprocessable Content, got {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)
        print("Unsupported format rejection correctly blocked with status 422.")

        # 4. Test Unauthenticated Access
        print("\n[4/4] Sending request without authorization headers (expecting 401)...")
        files = {"file": ("dirty_data.csv", csv_content, "text/csv")}
        res = await client.post("/api/v1/cleaning/analyze", files=files)
        if res.status_code != 401:
            print(f"Error: Expected 401 Unauthorized, got {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)
        print("Unauthenticated request correctly blocked with status 401.")

    print("\n=============================================================")
    print("DATA CLEANING VERIFIED SUCCESSFULLY")
    print("=============================================================")


if __name__ == "__main__":
    asyncio.run(run_cleaning_verification())

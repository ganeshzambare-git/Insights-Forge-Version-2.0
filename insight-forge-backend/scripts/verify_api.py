"""
Insight Forge V2 — API and Authentication Verification Script.

Tests FastAPI app startup, JWT login, and protected route access in-process.
"""

import asyncio
import sys
from httpx import AsyncClient, ASGITransport

# Set selector event loop on Windows to support psycopg async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app


async def run_api_verification() -> None:
    """Simulate user login and request execution against protected endpoints."""
    print("=============================================================")
    print("INSIGHT FORGE V2.2 — API & AUTH VERIFICATION SYSTEM")
    print("=============================================================")

    # Use ASGI Transport to run the app in-process
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test Welcome / Root Welcome Endpoint
        print("\n[1/4] Testing Welcome endpoint...")
        res = await client.get("/")
        if res.status_code != 200:
            print(f"Error: Welcome endpoint returned {res.status_code}", file=sys.stderr)
            sys.exit(1)
        print("Root response:", res.json())

        # 2. Test Swagger-compatible Authentication Endpoint
        print("\n[2/4] Testing /api/v1/auth/login...")
        login_data = {
            "corporate_email": "admin@insightforge.com",
            "password": "AdminSecurePassword123!",
            "remember_me": False,
        }
        res = await client.post("/api/v1/auth/login", json=login_data)
        if res.status_code != 200:
            print(f"Error: Login endpoint failed: {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)

        res_json = res.json()
        print("Login response structure parsed successfully.")
        
        token_data = res_json.get("data", {})
        access_token = token_data.get("access_token")
        if not access_token:
            print("Error: access_token not found in response payload.", file=sys.stderr)
            sys.exit(1)
        print("Successfully obtained JWT access token.")

        # 3. Test Protected Endpoint (List Users)
        print("\n[3/4] Testing protected endpoint /api/v1/users (authenticated)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        res = await client.get("/api/v1/users", headers=headers)
        if res.status_code != 200:
            print(f"Error: Protected route failed: {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)
        print("Protected route succeeded! User profiles list:")
        print(res.json())

        # 4. Assert Authentication Safeguard (Requesting without token)
        print("\n[4/4] Testing protected endpoint /api/v1/users (unauthenticated)...")
        res = await client.get("/api/v1/users")
        if res.status_code != 401:
            print(f"Error: Expected 401 Unauthorized, got {res.status_code}", file=sys.stderr)
            sys.exit(1)
        print("Unauthenticated access correctly blocked (401 Unauthorized).")

    print("\n=============================================================")
    print("API & AUTHENTICATION VERIFIED SUCCESSFULLY")
    print("=============================================================")


if __name__ == "__main__":
    asyncio.run(run_api_verification())

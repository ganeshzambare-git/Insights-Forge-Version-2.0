# API Design & Guidelines — Insight Forge V2

This document defines coding conventions, REST standards, and formatting guidelines for API endpoints in the Insight Forge V2 platform.

---

## 1. Routing Conventions

- Route paths must use **kebab-case** (e.g., `/api/v1/student-metrics`).
- All active routes must reside under the versioned `/api/v1/` prefix.
- Trailing slashes must be avoided in route definitions.
- Write thin routes: routes only validate request DTOs, check authorization, call services, and structure responses. No database or repository logic is allowed in controllers.

---

## 2. Standardized JSON Responses

Every successful REST response must be wrapped in a standardized envelope:

```json
{
  "success": true,
  "message": "Outcomes summary description.",
  "data": {
    "user_id": "uuid-value",
    "corporate_email": "user@test.com"
  },
  "meta": {
    "request_id": "req-id-uuid",
    "timestamp": "2026-07-08T23:50:58.000Z",
    "api_version": "2.0.0",
    "pagination": {
      "limit": 100,
      "offset": 0,
      "total": 1
    }
  },
  "errors": []
}
```

### Response HTTP Status Codes
- **POST**: `201 Created`
- **GET / PATCH**: `200 OK`
- **DELETE**: `204 No Content`

---

## 3. Exception Mapping

All service and operational errors map to consistent HTTP status codes:

- **Validation / DTO Error** (`ValidationError`): `422 Unprocessable Entity`
- **Credential Failure** (`AuthenticationError`): `401 Unauthorized`
- **RBAC / Tenant Violations** (`AuthorizationError`): `403 Forbidden`
- **Missing Aggregate** (`NotFoundError`): `404 Not Found`
- **State Conflict** (`ConflictError`): `409 Conflict`
- **Unhandled Operation Error**: `500 Internal Server Error`

Error envelopes match:

```json
{
  "success": false,
  "message": "Error description.",
  "data": {},
  "meta": {
    "request_id": "req-id-uuid",
    "timestamp": "2026-07-08T23:50:58.000Z",
    "api_version": "2.0.0"
  },
  "errors": [
    {
      "error": "error_code_identifier",
      "message": "Detail description of error."
    }
  ]
}
```

---

## 4. PATCH instead of PUT
To prevent full object replacement and protect RLS constraints, partial updates must use the HTTP `PATCH` verb. Update payloads support optional fields.

---

## 5. Security & Browser Headers
Every dynamic API response includes headers:
- `X-Request-ID`: Correlation tracing.
- `Cache-Control`: `no-store, no-cache, must-revalidate` (protecting dynamic sessions).
- `Strict-Transport-Security`: Enforcing HTTPS.

---

## 6. Future Extension Hooks (Documentation Only)
- **Bulk Operation Endpoints**: For future large data ingestion (`POST /users/bulk`, `POST /metrics/bulk`, `POST /interventions/bulk`).
- **Cursor Pagination**: Supporting large datasets with `cursor` parameters.
- **Caching & Rate Limiting**: Extension hooks to add Redis cache headers or rate limit policies.

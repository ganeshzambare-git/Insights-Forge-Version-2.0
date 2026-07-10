# Master Memory — Insight Forge V2

> **Read this first.** Compressed project intelligence for AI agents. Target: under 5,000 words.
> Last updated: 2026-07-10

## What This Project Is

**Insight Forge V2** is an enterprise multi-tenant educational intelligence platform. It manages institutional data (tenants, users, cohorts, student metrics, coaching interventions), provides academic analytics and risk classification, and runs a multi-agent AI pipeline over uploaded datasets.

**Stack:** FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 (RLS) + Next.js 14 (minimal frontend).

**Root:** `insight-forge-Version_2/` containing `insight-forge-backend/` and `insight-forge-frontend/`.

---

## Architecture Summary

```
Next.js Frontend → REST /api/v1/* → FastAPI Endpoints
    → Auth Guards (JWT + RBAC) → Services (business logic + UoW)
    → Repositories (data access) → PostgreSQL + RLS
```

**Middleware order:** TrustedHost → CORS → GZip → RequestID → SecurityHeaders → Timing → Tenant.

**Tenant isolation:** `TenantMiddleware` sets context; DB uses `SET LOCAL app.current_tenant_id` for RLS policies on cohorts, metrics, interventions, users, sessions.

**Roles:** Admin, Dean, Faculty, Student.

---

## Key Decisions

| Decision | Why |
|----------|-----|
| PostgreSQL RLS | Defense-in-depth tenant isolation at DB level |
| psycopg3 async | SQLAlchemy 2.0 async on Neon/production |
| Synchronous analytics | No Celery dependency (free-tier hosting constraints) |
| Mock LLM default | AI pipeline works without external API keys |
| PATCH not PUT | Partial updates; RLS-safe |
| JTI-only session storage | No raw tokens in DB; rotation + reuse detection |
| `python serve.py` on Windows | psycopg3 incompatible with ProactorEventLoop |

---

## Approved Patterns

- **Repository:** Stateless CRUD in `app/repositories/`. No commit/rollback.
- **UnitOfWork:** `async with uow` in services for transaction boundaries.
- **Command/Query:** Commands return `ServiceResult[T]`; queries return entities directly.
- **DI:** FastAPI `Depends` factories in `app/dependencies/services.py`.
- **API envelope:** `{success, message, data, meta, errors}` via `api_response()`.
- **AI agents:** Immutable `AIContext` with `evolve()`; sequential orchestration.

---

## Feature Status

| Area | Status |
|------|--------|
| Multi-tenant CRUD (tenants, users, cohorts, metrics, interventions) | ✅ Implemented |
| JWT auth + DB sessions | ✅ Implemented |
| Academic analytics / risk classification | ✅ Implemented |
| AI multi-agent pipeline | ✅ Implemented (mock LLM) |
| Data cleaning pipeline | ✅ Implemented |
| Frontend | ✅ Implemented (Dashboard + Login ingress + Session purge overlay + Admin console) |
| Dataset Ingestion API | ⚠️ Chunk Streams (Task 9 uploader telemetry endpoint completed) |
| Connectivity Resilience & Executive Canvas | ✅ Implemented (exponential backoff heartbeats + Dean KPI canvas + skeletons + timeouts) |
| Simulation Sandbox, Exports & Virtualized Tables | ✅ Implemented (Task 13 debounced sandbox + Task 14 background export + Task 15 virtual roster) |
| Faculty Search, Risk Indicators & Interventions | ✅ Implemented (Task 16 debounced search + Task 17 ML badges + Task 18 focus-locked drawer) |
| Student Dashboards, Curves & Protected Guards | ✅ Implemented (Task 19 progress dashboard + Task 20 comparative line curves + Task 21 route guards) |
| Reports API | ❌ Placeholder |
| Redis/Celery workers | ❌ Config only, stubs |

---

## API Surface (all `/api/v1`)

- `/auth` — login, refresh, logout, me
- `/tenants`, `/users`, `/cohorts`, `/metrics`, `/interventions` — CRUD
- `/analytics` — dashboard, KPIs, risk, performance, trends, recommendations
- `/ai/analyze` — file upload → multi-agent pipeline
- `/cleaning/analyze` — file upload → cleaning pipeline
- `/health` — health check
- `/datasets`, `/ingestion`, `/reports` — **placeholders**

---

## AI Pipeline

Sequential agents: Data Engineer → Data Analyst → Business Analyst → Executive Report.

Entry: `POST /api/v1/ai/analyze` → `AIService` → `AIWorkflowOrchestrator` → agents in `app/ai/agents/`.

Default LLM: `DefaultLLMProvider` (mock structured output).

---

## Known Issues

1. **Windows:** Use `python serve.py`, not `uvicorn` directly.
2. **Docker DB URL:** compose uses `postgresql+asyncpg://`; app rewrites to `postgresql+psycopg://` — use plain `postgresql://` in `DATABASE_URL`.
3. **Frontend mock token:** `page.tsx` sends `Bearer mock-session-token-admin` — fails against real JWT auth.
4. **Stale backend README:** Checklist outdated; most layers are implemented.
5. **JWT algorithm:** README says RS256; config defaults HS256.

---

## Roadmap Snapshot

**Next priorities:**
- Real LLM provider integration
- Frontend auth flow and analytics dashboards
- Dataset ingestion and reports APIs
- Bulk endpoints (`/users/bulk`, `/metrics/bulk`)
- Redis caching layer

**Future:** WebSockets, OpenTelemetry, cursor pagination, RS256 JWT with key files.

---

## Key Entry Points

| Purpose | Path |
|---------|------|
| Backend entry | `insight-forge-backend/app/main.py` |
| API router | `insight-forge-backend/app/api/v1/router.py` |
| Config | `insight-forge-backend/app/core/config.py` |
| Windows dev server | `insight-forge-backend/serve.py` |
| Frontend | `insight-forge-frontend/src/app/page.tsx` |
| Architecture docs | `insight-forge-backend/docs/architecture/` |
| Docker | `docker-compose.yml` |

---

## Before You Code

1. Read `architecture.md` for layer boundaries.
2. Read `patterns.md` for implementation conventions.
3. Read `decisions.md` before proposing architectural changes.
4. Check `feature-map.md` to find existing implementations.
5. Check `mistakes.md` to avoid known failures.
6. After completing work, update relevant brain files.

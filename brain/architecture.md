# Architecture — Insight Forge V2

> Complete architectural understanding. Read before making structural changes.
> Last updated: 2026-07-10

## System Overview

Insight Forge is a monorepo with a FastAPI backend and Next.js frontend, orchestrated via Docker Compose.

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│              (insight-forge-frontend/)                   │
│         Single page: AI upload dashboard                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP REST
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│              (insight-forge-backend/)                    │
│                                                          │
│  Middleware Stack → API Layer → Service Layer          │
│       → Repository Layer → PostgreSQL + RLS            │
│                                                          │
│  AI Subsystem: Orchestrator → Agents → LLM Provider    │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    PostgreSQL 16   Redis 7     (Celery stub)
    (with RLS)    (configured)
```

## Backend Layer Architecture

### Layer 1: Middleware (`app/middleware/`)

Applied in order (see `app/main.py`):

| Middleware | Purpose |
|------------|---------|
| TrustedHostMiddleware | Host header validation |
| CORSMiddleware | Cross-origin requests |
| GZipMiddleware | Response compression |
| RequestIDMiddleware | Unique request ID per request |
| SecurityHeadersMiddleware | Security response headers |
| TimingMiddleware | Request duration tracking |
| TenantMiddleware | Extract tenant from JWT or `X-Tenant-ID` header |

### Layer 2: API (`app/api/v1/`)

```
app/api/v1/
├── router.py           # Consolidated router mounting all endpoints
├── endpoints/          # Thin controllers — validation + delegation only
│   ├── auth.py
│   ├── users.py
│   ├── tenants.py
│   ├── cohorts.py
│   ├── metrics.py
│   ├── interventions.py
│   ├── analytics.py
│   ├── ai.py
│   ├── cleaning.py
│   ├── health.py
│   ├── datasets.py     # placeholder
│   ├── ingestion.py    # placeholder
│   └── reports.py      # placeholder
└── schemas/            # Request/response DTOs (API-level)
```

**Rules:**
- No database access in endpoints
- No business logic in endpoints
- All responses use `api_response()` envelope
- RBAC via `RequireRoles(Role.ADMIN, ...)` dependency
- Use PATCH for updates, not PUT

### Layer 3: Services (`app/services/`)

| Service | Responsibility |
|---------|---------------|
| `AuthService` | Login, token refresh, logout |
| `SessionService` | JWT session lifecycle, JTI management |
| `UserService` | User CRUD, password management |
| `TenantService` | Tenant CRUD |
| `CohortService` | Cohort management |
| `StudentMetricService` | Academic metric tracking |
| `CoachingInterventionService` | Intervention logging |
| `AnalyticsService` | Dashboards, KPIs, risk classification |
| `AIService` | File upload → AI pipeline orchestration |
| `CleaningService` | File upload → cleaning pipeline |

**Transaction management:**
```python
async with uow:
    result = await service.execute_command(...)
    # auto-commit on exit, rollback on exception
```

### Layer 4: Repositories (`app/repositories/`)

Generic `BaseRepository` with CRUD operations. Stateless — no commit/rollback.

| Repository | Entity |
|------------|--------|
| `TenantRepository` | Tenant |
| `UserRepository` | User |
| `SessionRepository` | Session |
| `CohortRepository` | Cohort |
| `StudentMetricRepository` | StudentMetric |
| `CoachingInterventionRepository` | CoachingIntervention |

### Layer 5: Database (`app/db/` + `app/models/`)

**ORM Models:**
- `Tenant` — institutional partner (global, no RLS)
- `User` — tenant-scoped user with role
- `Session` — JWT session tracking (JTI, expiry, IP)
- `Cohort` — student group within tenant
- `StudentMetric` — academic records per student
- `CoachingIntervention` — advisory logs

**Connection:**
- Engine: `app/db/engine.py`
- Sessions: `app/db/session.py` (async, tenant context injection)
- Tenant context: `app/db/tenant_context.py` (ContextVar)
- Encrypted columns: `app/db/types/encrypted.py` (EncryptedString)

**RLS Policies:**
- Strict: `cohorts`, `student_metrics`, `coaching_interventions`
- Permissive: `users`, `sessions`
- Mechanism: `SET LOCAL app.current_tenant_id = '<uuid>'`

## Authentication Architecture

```
Client → POST /api/v1/auth/login
    → AuthService validates credentials
    → SessionService creates DB session (stores JTI)
    → Returns access_token + refresh_token

Subsequent requests:
    → TenantMiddleware extracts tenant_id
    → get_current_session validates JWT (signature, type, JTI in DB)
    → get_current_user loads user from session
    → RequireRoles checks RBAC
```

**JWT Claims:** `sub`, `tenant_id`, `role`, `jti`, `type`, `iss`, `aud`, `iat`, `nbf`, `exp`

**Security files:** `app/core/security/jwt.py`, `passwords.py`, `encryption.py`

## AI Subsystem Architecture

```
app/ai/
├── agents/              # Pipeline stage implementations
│   ├── data_engineer.py
│   ├── data_analyst.py
│   ├── business_analyst.py
│   └── executive_report.py
├── contracts/           # BaseAIAgent interface
├── context/             # Immutable AIContext model
├── llm/                 # LLM provider abstraction
│   ├── provider.py      # BaseLLMProvider
│   └── default.py       # DefaultLLMProvider (mock)
├── orchestration/       # AIWorkflowOrchestrator
├── utils/               # Cleaning, profiling utilities
└── schemas/             # AI-specific Pydantic models
```

**Pipeline flow:**
1. File uploaded to `POST /api/v1/ai/analyze`
2. `AIService` parses file, creates initial `AIContext`
3. `AIWorkflowOrchestrator` runs agents sequentially
4. Each agent receives context, calls LLM, returns evolved context
5. Final result: `OrchestratedPipelineResult` with consolidated report

## Analytics Architecture

Deterministic risk classification (not ML):

| Risk Tier | Criteria |
|-----------|----------|
| Safe | GPA ≥ 3.0, attendance ≥ 85%, ≤ 1 intervention |
| Amber | GPA 2.0–3.0 or attendance 70–85% or 2 interventions |
| Critical | GPA < 2.0 or attendance < 70% or ≥ 3 interventions |

Health Score: weighted index from risk distribution across institution.

See `docs/architecture/analytics.md` for full formulas.

## Frontend Architecture

Minimal Next.js 14 App Router setup:

```
insight-forge-frontend/src/app/
├── layout.tsx    # Root layout
├── page.tsx      # Single AI upload dashboard
└── globals.css   # Global styles
```

No component library, no routing library, no state management. Intentionally minimal.

**API communication:** Direct `fetch` to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Infrastructure

**Docker Compose services:**
- `postgres` — PostgreSQL 16 on port 5432
- `redis` — Redis 7 on port 6379
- `backend` — FastAPI on port 8000
- `frontend` — Next.js on port 3000

**Detailed docs:** `insight-forge-backend/docs/architecture/` (9 files covering every layer).

## Dependency Injection

All services injected via FastAPI `Depends`:

```python
# app/dependencies/services.py
def get_user_service(ctx: ServiceContext = Depends(get_service_context)) -> UserService:
    return UserService(ctx)
```

Auth guards in `app/dependencies/auth.py`:
- `get_current_session` — JWT + DB session validation
- `get_current_user` — User entity from session
- `RequireRoles(*roles)` — RBAC enforcement class

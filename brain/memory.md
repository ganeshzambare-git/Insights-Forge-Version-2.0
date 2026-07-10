# Project Memory — Insight Forge V2

> Central project summary. Updated after every significant task.
> Last updated: 2026-07-10

## What the Project Does

Insight Forge V2 is an enterprise-grade **multi-tenant educational intelligence platform**. It serves institutional partners (tenants) who manage student cohorts, track academic metrics, log coaching interventions, and view analytics dashboards with risk classification.

Additionally, it provides:
- **AI decision intelligence** — upload CSV/JSON datasets through a multi-agent pipeline that produces executive reports
- **Data quality tooling** — cleaning and profiling pipeline for uploaded files

## Key Features

### Institutional Data Management
- Tenant provisioning and configuration
- User management with role-based access (Admin, Dean, Faculty, Student)
- Cohort management within tenant scope
- Student metric tracking (GPA, attendance, risk status)
- Coaching intervention logging with encrypted notes

### Academic Analytics
- Institutional dashboard and KPIs
- Student risk classification (Safe / Amber / Critical)
- Cohort and faculty performance views
- Trend analysis and recommendations
- Deterministic risk rules (not ML-based)

### AI Pipeline
- Sequential multi-agent workflow: Data Engineer → Data Analyst → Business Analyst → Executive Report
- File upload via REST API
- Mock LLM provider by default (no API keys required)

### Data Cleaning
- CSV/XLSX upload and analysis
- Quality scoring and audit logging
- Trusted dataset output

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 async, psycopg3 |
| Database | PostgreSQL 16 with Row-Level Security |
| Auth | JWT (HS256 default), bcrypt, DB-backed sessions |
| Frontend | Next.js 14, React 18, TypeScript |
| Infra | Docker Compose (postgres, redis, backend, frontend) |
| Quality | pytest, ruff, mypy (strict), black |

## Current State

### Implemented
- Full layered backend: API → Service → Repository → Database
- JWT authentication with session management (JTI tracking)
- Multi-tenant isolation via middleware + RLS
- Public tenant subdomain verification endpoint (`GET /api/v1/tenants/verify/{slug}`)
- Observability API endpoint (`GET /api/v1/admin/cluster-metrics`) for compute performance
- Key rotation (`POST /api/v1/admin/rotate-keys`) and rate limit logs (`GET /api/v1/admin/rate-limit-logs`) admin endpoints
- Chunked dataset ingestion telemetry endpoint (`POST /api/v1/ingest/upload-telemetry`)
- All core CRUD endpoints for tenants, users, cohorts, metrics, interventions
- Analytics service with risk classification
- AI multi-agent pipeline with orchestrator
- Data cleaning pipeline
- Comprehensive unit test suite (22 test files)
- Architecture documentation (9 docs in `docs/architecture/`)
- Frontend multi-tenant workspace ingress and secure credentials login pages
- Phase 2 Security Lifecycle: 15-minute session timeout overlay controller and workspace redirection gateway
- Zero-Trust DOM rendering engine guards (`RoleGuard` and `PermissionGuard`)
- Admin observability console featuring CPU utilization progress bars and dynamic request volume area charts
- Task 7: Cryptographic SSO Key Rotation Page featuring a focus-trapping modal and two-step confirmation flow
- Task 8: Tenant Rate Limit Observatory Dashboard containing a visual timeline, 44x44 touch-target sliders, and Alert Crimson alerts
- Task 9: Large Ingestion Dataset Client supporting 1MB chunked uploads, AbortController cancellation triggers, and client-side CSV column schema checks
- Task 10: Server Connection Resilience provider polling /health with 1s->2s->4s->8s->16s exponential backoff and 40% dimmed dialog overlays
- Task 11: Institutional Executive KPI Canvas presenting student cohorts averages and compute allocations using custom lightweight SVGs
- Task 12: High-Density Department Filter Panel displaying light gray loading skeletons and 2.5s network timeout refiners
- Task 13: Out-of-Band Planning Sandbox Simulator with left-aligned slider controls, 300ms debouncing, and SVG prediction charts
- Task 14: Academic Audit Package Export non-blocking panels with simulated background compilation intervals and secure download alerts
- Task 15: Virtualized student roster container calculating scroll offsets to slice DOM row nodes (retaining sticky header positions)
- Task 16: Asynchronous Cohort Search with 300ms debounced inputs, query abort signals, and Ocean Blue row highlights on hover/focus
- Task 17: Machine Learning Risk Indicator Badges mapping Amber and Critical statuses to WCAG-compliant high contrast warning cards
- Task 18: Focus-Trapped Coaching Intervention side drawer capturing and restoring keyboard targets, validating note length inputs
- Task 19: Student Personal Progress Dashboard with target term selectors and monospace metadata parameters
- Task 20: Student Performance Distribution comparisons utilizing responsive curves inside white container card layouts with a 4px border-radius
- Task 21: Client-side Cross-Role Navigation Route Guards redirecting users on role checks, clearing states, and rendering Alert Crimson warnings

### Partial / Minimal
- Redis/Celery: configured but not integrated (health shows "pending")
- Background workers: stub implementations

### Not Started / Placeholder
- Reports API (`/reports`)
- Real LLM provider implementations
- MFA flow (fields exist on User model, no endpoints)
- Bulk import endpoints

## Active Work

- **Phase 2 Complete**: Next phase planning.

## Repository Structure

```
insight-forge-Version_2/
├── AGENTS.md
├── brain/                     ← Project Brain (you are here)
├── workflows/
├── docker-compose.yml
├── insight-forge-backend/     ← FastAPI application
│   ├── app/                   ← Application code
│   ├── docs/architecture/     ← Detailed architecture docs
│   ├── migrations/            ← Alembic migrations
│   ├── scripts/               ← Bootstrap, seed, verify scripts
│   └── tests/                 ← Unit + integration tests
└── insight-forge-frontend/    ← Next.js application
    └── src/app/               ← App Router pages
```

## Development Setup

1. Copy `.env.example` to `.env` in backend root
2. Set `DATABASE_URL` (PostgreSQL connection string)
3. Run migrations: `alembic upgrade head`
4. **Windows:** `python serve.py` (not `uvicorn` directly)
5. **Linux/Docker:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`
6. Frontend: `npm run dev` in `insight-forge-frontend/`
7. Or use `docker-compose up` for full stack

## Test Commands

```bash
cd insight-forge-backend
pytest                          # all tests
pytest tests/unit/test_auth.py  # specific test
ruff check .                    # lint
```

## Related Brain Files

- Architecture details → `architecture.md`
- Implementation patterns → `patterns.md`
- Engineering decisions → `decisions.md`
- Feature-to-file mapping → `feature-map.md`
- Known failures → `mistakes.md`
- Future direction → `roadmap.md`

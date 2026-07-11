# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Brain (read before non-trivial work)

This repo maintains its own persistent knowledge base in `brain/`. It is the source of truth for
architecture and conventions — prefer it over re-deriving from a full repo scan. Read in this order:

1. `brain/master-memory.md` — compressed project intelligence (start here)
2. `brain/architecture.md` — layer boundaries and system design
3. `brain/patterns.md` — approved implementation patterns (with code)
4. `brain/decisions.md` — engineering decisions and rationale

As needed: `brain/feature-map.md` (find files), `brain/mistakes.md` (known gotchas),
`brain/dependency-graph.md`, `brain/glossary.md`, `brain/roadmap.md`.
`AGENTS.md` defines the agent workflow and hard rules. Detailed per-layer docs live in
`insight-forge-backend/docs/architecture/` (10 files).

**After completing work that changes architecture, patterns, or fixes a recurring mistake, update the
relevant `brain/*.md` files** (and re-compress `master-memory.md` after significant changes).

## What this is

**Insight Forge V2** — a multi-tenant educational decision-intelligence platform. Monorepo:

- `insight-forge-backend/` — FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 (Row-Level Security). The bulk of the code.
- `insight-forge-frontend/` — minimal Next.js 14 App Router UI (Login, Admin, Student pages).
- `brain/`, `workflows/` — project intelligence and process artifacts.

## Commands

Backend (run from `insight-forge-backend/`):

```bash
pip install -e ".[dev]"          # install deps — pyproject.toml is authoritative (requirements.txt is stale/minimal)
python serve.py                   # run dev server on 127.0.0.1:8000 (see event-loop note below)
pytest                            # run all tests
pytest tests/unit/test_auth.py    # run one test file
pytest tests/unit/test_auth.py::test_name   # run one test
ruff check .                      # lint
mypy app                          # type-check (configured strict)
alembic upgrade head              # apply migrations
alembic revision --autogenerate -m "msg"   # create migration
python scripts/bootstrap.py       # create DB + run migrations + seed (idempotent)
```

Frontend (run from `insight-forge-frontend/`):

```bash
npm install
npm run dev        # dev server on :3000
npm run build      # production build; backend can serve the static export from ./out
npm run lint
```

Note: the root `Makefile` and `.github/workflows/backend-ci.yml` are empty stubs — do not rely on them.

## Critical run/dev notes

- **Always start the backend via `python serve.py`, not raw `uvicorn`.** psycopg3 async needs a
  `SelectorEventLoop`; on Windows the Proactor loop raises `InterfaceError`. `serve.py` and `main.py`
  set the selector policy. On Linux prod, `uvicorn app.main:app --host 0.0.0.0 --port 8000` is fine.
- **`DATABASE_URL` must be plain `postgresql://...`** (the app rewrites the driver to `psycopg`).
  Do not put `+asyncpg` or `+psycopg` in the URL. Neon connection strings need `?sslmode=require`.
- Python **3.13** required (`>=3.13,<3.14`). Copy `.env.example` → `.env` in the backend dir.

## Backend architecture (layered — respect the boundaries)

Request flow: **Middleware → API endpoint → Service → Repository → PostgreSQL (RLS)**.

- **Middleware** (`app/middleware/`, wired in `app/main.py`), applied in order: TrustedHost → CORS →
  GZip → RequestID → SecurityHeaders → Timing → **Tenant**. `TenantMiddleware` extracts tenant from
  the JWT or `X-Tenant-ID` header and sets the request tenant context.
- **API** (`app/api/v1/`): `router.py` mounts thin controllers in `endpoints/`. Endpoints do
  **validation + delegation only** — no DB access, no business logic. All responses go through the
  `api_response()` envelope. `datasets.py`, `ingestion.py`, `reports.py` are placeholders.
- **Services** (`app/services/`): all business logic. Injected via `Depends` factories in
  `app/dependencies/services.py`. `ServiceContext` bundles session, UoW, audit logger, providers.
- **Repositories** (`app/repositories/`): stateless CRUD extending `BaseRepository`.
  **Never commit/rollback here** — transactions belong to the UnitOfWork in services.
- **DB/models** (`app/db/`, `app/models/`): async engine/session with tenant-context injection;
  `EncryptedString` column type for PII.

Key conventions (details + code in `brain/patterns.md`):

- **Tenant isolation is enforced by PostgreSQL RLS** via `SET LOCAL app.current_tenant_id = '<uuid>'`.
  When the tenant context is set, queries are auto-scoped — no manual tenant filtering. Never bypass it.
- **Transactions**: write operations (commands) run inside `async with uow:` (auto-commit / auto-rollback).
  Commands return `ServiceResult[T]`; queries return entities directly.
- **Errors**: services raise domain exceptions (`NotFoundError`, `ConflictError`, `ValidationError`,
  `AuthenticationError`, `AuthorizationError`, …); endpoints never catch — global handlers in
  `app/main.py` map them to HTTP status codes. Never raise `HTTPException` from a service.
- **Use PATCH, not PUT** for updates (partial, RLS-safe).
- **RBAC**: guard endpoints with `Depends(RequireRoles(Role.ADMIN, ...))`. Roles: Admin, Dean, Faculty,
  Student (`app/core/roles.py`).
- **Auth**: `POST /api/v1/auth/login` returns access (15 min) + refresh (7 day) tokens. Only the JTI is
  stored in the DB (not raw tokens); refresh rotates the JTI with reuse detection.

## AI subsystem (`app/ai/`)

`POST /api/v1/ai/analyze` uploads a file → `AIService` builds an initial immutable `AIContext` →
`AIWorkflowOrchestrator` runs agents **sequentially**: Data Engineer → Data Analyst → Business Analyst
→ Executive Report. Each agent calls an `BaseLLMProvider` and returns an **evolved** context
(`context.evolve(...)` — never mutate). Default provider `DefaultLLMProvider` returns mock structured
output, so the pipeline runs with no API key. To add a real LLM, implement `BaseLLMProvider` and inject
it in `AIService`. Analytics/risk classification (`app/services` + `app/analytics`) is **deterministic
rule-based, not ML**.

## Testing

`tests/unit/` mirrors source (`test_auth.py` ↔ `auth.py`). `pytest` runs in `asyncio_mode = auto`.
Unit tests mock repositories and the swappable providers (LLM, clock, UUID via `app/services/providers.py`).
Fixtures in `tests/conftest.py`.

## Known issues / gotchas (see `brain/mistakes.md`)

- Backend `README.md` status checklist is **outdated** — most layers are implemented.
- README claims RS256 JWT, but config defaults to **HS256**.
- Frontend `page.tsx` may send `Bearer mock-session-token-admin`, which fails real JWT auth.
- Redis/Celery are config/stubs only — background work is synchronous (free-tier hosting constraint).

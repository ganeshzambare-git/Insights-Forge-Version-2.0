# Decisions — Insight Forge V2

> Important engineering decisions and their rationale.
> Last updated: 2026-07-10

## Database & Infrastructure

### Decision: PostgreSQL with Row-Level Security

**Date:** Initial architecture
**Status:** Active

**Decision:** Use PostgreSQL RLS for tenant isolation at the database level, not just application-level filtering.

**Reason:**
- Defense-in-depth: even if application code has a bug, DB enforces isolation
- `SET LOCAL app.current_tenant_id` per request via `TenantMiddleware`
- Strict policies on data tables; permissive on auth tables

**Alternatives considered:**
- Application-only filtering (rejected: single point of failure)
- Separate databases per tenant (rejected: operational complexity)

**Files:** `migrations/versions/9092070a0ca7_initial_schema.py`, `app/db/tenant_context.py`

---

### Decision: psycopg3 Async Driver

**Date:** Initial architecture
**Status:** Active

**Decision:** Use psycopg3 (`postgresql+psycopg://`) as the async database driver.

**Reason:**
- Native async support with SQLAlchemy 2.0
- Compatible with Neon serverless PostgreSQL
- Better performance than asyncpg for this stack

**Alternatives considered:**
- asyncpg (used in docker-compose but app rewrites URL to psycopg)
- psycopg2 (rejected: synchronous only)

**Files:** `app/core/config.py` (URL rewriting), `app/db/engine.py`

---

### Decision: Neon PostgreSQL for Production

**Date:** Initial architecture
**Status:** Active

**Decision:** Target Neon serverless PostgreSQL for production deployment.

**Reason:** Serverless scaling, connection pooling, SSL by default.

**Config:** `DATABASE_URL` with `?sslmode=require`

---

## Architecture

### Decision: Layered Architecture (API → Service → Repository)

**Date:** Initial architecture
**Status:** Active

**Decision:** Strict three-layer architecture with no business logic in API layer.

**Reason:**
- Testability: each layer independently testable
- Maintainability: clear responsibility boundaries
- Consistency: every feature follows the same structure

**Rules:**
- Endpoints: validation + delegation only
- Services: business logic + transaction management
- Repositories: data access only

**Files:** `docs/architecture/backend_architecture.md`, all of `app/services/`, `app/repositories/`

---

### Decision: Synchronous Analytics (No Celery)

**Date:** Initial architecture
**Status:** Active

**Decision:** Run analytics computations synchronously in the request cycle. Do not use Celery for BI operations.

**Reason:**
- Free-tier hosting constraints (Render/Railway)
- Analytics queries are fast enough for synchronous execution
- Avoids operational complexity of worker processes

**Alternatives considered:**
- Celery + Redis workers (deferred to future phase)
- FastAPI BackgroundTasks (preferred if async needed later)

**Files:** `docs/architecture/analytics.md`, `app/services/analytics.py`

---

### Decision: PATCH Not PUT

**Date:** API design
**Status:** Active

**Decision:** Use PATCH for all update operations. Never expose PUT endpoints.

**Reason:**
- Partial updates are the common case
- PUT risks accidental full-replacement
- Safer with RLS policies (only changed fields evaluated)

**Files:** `docs/architecture/api_guidelines.md`, all update endpoints

---

## Security

### Decision: JTI-Only Session Storage

**Date:** Authentication design
**Status:** Active

**Decision:** Store JWT ID (JTI) in database, not raw tokens. Implement token rotation and reuse detection.

**Reason:**
- Tokens can be revoked by deleting session record
- Refresh rotation prevents token theft reuse
- No sensitive token material persisted

**Alternatives considered:**
- Stateless JWT only (rejected: no revocation)
- Full token storage (rejected: security risk)

**Files:** `docs/architecture/authentication.md`, `app/services/session.py`, `app/core/security/jwt.py`

---

### Decision: EncryptedString for Sensitive Columns

**Date:** Schema design
**Status:** Active

**Decision:** Use application-level encryption (`EncryptedString` type) for `totp_secret` and `intervention_notes`.

**Reason:** PII and secrets encrypted at rest, independent of DB-level encryption.

**Files:** `app/db/types/encrypted.py`, migration schema

---

### Decision: HS256 JWT Default (RS256 Supported)

**Date:** Authentication design
**Status:** Active

**Decision:** Default to HS256 symmetric signing. Support RS256 via key file configuration.

**Reason:** Simpler dev setup with single `SECRET_KEY`. RS256 available for production via `JWT_PRIVATE_KEY_PATH` / `JWT_PUBLIC_KEY_PATH`.

**Note:** README env example shows RS256 but config defaults HS256. Use config.py as source of truth.

**Files:** `app/core/config.py`, `app/core/security/jwt.py`

---

## AI System

### Decision: Mock LLM Provider by Default

**Date:** AI subsystem design
**Status:** Active

**Decision:** `DefaultLLMProvider` returns structured mock data. No external API keys required.

**Reason:**
- Pipeline fully testable without API costs
- Development and CI work out of the box
- Real providers added via `BaseLLMProvider` interface

**Files:** `app/ai/llm/default.py`, `app/services/ai_service.py`

---

### Decision: Immutable AI Context

**Date:** AI subsystem design
**Status:** Active

**Decision:** `AIContext` is a frozen Pydantic model. State transitions via `evolve()` method.

**Reason:**
- Prevents accidental mutation between agents
- Clear audit trail of context evolution
- Thread-safe by design

**Files:** `app/ai/context/model.py`

---

### Decision: Sequential Agent Pipeline

**Date:** AI subsystem design
**Status:** Active

**Decision:** Agents execute sequentially, not in parallel. Each agent receives output from the previous.

**Reason:**
- Each stage depends on prior analysis
- Simpler error handling and debugging
- Per-agent timing metrics for observability

**Files:** `app/ai/orchestration/orchestrator.py`

---

## Development

### Decision: Windows SelectorEventLoop

**Date:** Development environment
**Status:** Active

**Decision:** On Windows, use `python serve.py` which sets `WindowsSelectorEventLoopPolicy` before starting uvicorn.

**Reason:** psycopg3 is incompatible with Windows ProactorEventLoop. Direct `uvicorn` invocation causes `InterfaceError`.

**Files:** `serve.py`, `app/main.py` (lifespan hook), `README.md`

---

### Decision: Standard API Response Envelope

**Date:** API design
**Status:** Active

**Decision:** All API responses use `{success, message, data, meta, errors}` envelope.

**Reason:** Consistent client-side error handling. Meta field supports pagination.

**Files:** `app/utils/response.py`, `docs/architecture/api_guidelines.md`

---

### Decision: Audit Logging per Operation

**Date:** Service layer design
**Status:** Active

**Decision:** Every service command logs started/succeeded/failed lifecycle events.

**Reason:** Operational visibility. Future hook for OpenTelemetry/Prometheus.

**Files:** `app/services/audit.py`

---

## Frontend

### Decision: Minimal Frontend (No Component Library)

**Date:** Frontend design
**Status:** Active

**Decision:** Single-page Next.js app with no UI framework, no routing library, no state management.

**Reason:** Backend-first development. Frontend is a thin demo for AI upload. Full UI deferred.

**Files:** `insight-forge-frontend/src/app/page.tsx`

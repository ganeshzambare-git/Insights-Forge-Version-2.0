# Mistakes — Insight Forge V2

> Known failures, gotchas, and fixes. Read before debugging or implementing.
> Last updated: 2026-07-10

## Resolved Issues

### Windows Event Loop Crash

**Problem:** Running `uvicorn app.main:app` directly on Windows causes `InterfaceError` from psycopg3.

**Cause:** Windows defaults to `ProactorEventLoop` which is incompatible with psycopg3 async operations.

**Fix:** Use `python serve.py` which sets `WindowsSelectorEventLoopPolicy` before uvicorn starts. Alternatively, `app/main.py` lifespan also sets this policy.

**Status:** Resolved — documented in README and serve.py

**Prevention:** Always use `serve.py` on Windows. Never document `uvicorn` as the Windows dev command.

---

### Docker DATABASE_URL Driver Mismatch

**Problem:** Docker Compose sets `DATABASE_URL=postgresql+asyncpg://...` but the application rewrites URLs to `postgresql+psycopg://`.

**Cause:** `app/core/config.py` normalizes all database URLs to psycopg3 driver. Docker compose was configured with asyncpg.

**Fix:** Use plain `postgresql://` in `DATABASE_URL` (no driver prefix). The config layer handles driver selection.

**Status:** Known — docker-compose.yml still uses asyncpg prefix

**Prevention:** When configuring DATABASE_URL, use `postgresql://user:pass@host/db` without driver prefix.

---

## Active Gotchas

### Frontend Mock Auth Token

**Problem:** `insight-forge-frontend/src/app/page.tsx` sends `Authorization: Bearer mock-session-token-admin` which fails against the real JWT auth backend.

**Cause:** Frontend was built as a demo without real auth integration.

**Impact:** AI upload page returns 401 against a running backend with real auth.

**Workaround:** Temporarily disable auth on AI endpoint for demo, or implement real login flow.

**Status:** Open — frontend auth not implemented

---

### Stale Backend README Checklist

**Problem:** `insight-forge-backend/README.md` shows Repository, Service, Auth, API as incomplete ([ ]), but code is largely implemented.

**Cause:** README not updated as development progressed.

**Impact:** New developers/agents underestimate project completeness.

**Workaround:** Trust Project Brain and code over README checklist.

**Status:** Open — README needs update

---

### JWT Algorithm Documentation Mismatch

**Problem:** README env example specifies `JWT_ALGORITHM="RS256"` but `app/core/config.py` defaults to `HS256`.

**Cause:** RS256 support was added later; README not updated.

**Impact:** Confusion about which algorithm is active.

**Workaround:** Check `config.py` defaults. RS256 requires `JWT_PRIVATE_KEY_PATH` and `JWT_PUBLIC_KEY_PATH` env vars.

**Status:** Open — documentation inconsistency

---

### Placeholder API Routers

**Problem:** `/api/v1/datasets`, `/api/v1/ingestion`, and `/api/v1/reports` are mounted in the router but contain no endpoints.

**Cause:** Future features scaffolded early.

**Impact:** Clients calling these paths get empty responses or 404.

**Workaround:** Do not implement client code against these paths until endpoints exist.

**Status:** Open — by design (future work)

---

### Redis/Workers Health Shows "pending"

**Problem:** Health endpoint reports Redis and background workers as `"pending"`.

**Cause:** Redis is configured in docker-compose but not integrated into application code. Celery worker not in docker-compose.

**Impact:** Health check is partially informative only.

**Workaround:** Treat Redis/worker status as informational, not blocking.

**Status:** Open — deferred to future phase

---

### Analytics Pipeline Stub

**Problem:** `app/pipelines/analytics_pipeline.py` returns `None`.

**Cause:** Background analytics processing deferred (synchronous analytics chosen instead).

**Impact:** No background analytics processing. All analytics run in request cycle.

**Workaround:** Use `AnalyticsService` directly for all analytics needs.

**Status:** Open — intentional (see decisions.md: synchronous analytics)

---

### Default Secrets in Docker Compose

**Problem:** `docker-compose.yml` uses `default-secret-key-32-characters-long-secret` for JWT/SECRET_KEY.

**Cause:** Development convenience.

**Impact:** Must never use docker-compose secrets in production.

**Workaround:** Override via environment variables or `.env` file for any non-local deployment.

**Status:** Open — dev only, documented here

---

### MFA Fields Without Flow

**Problem:** User model has `is_mfa_enabled` and `totp_secret` (EncryptedString) but no MFA endpoints exist.

**Cause:** Schema prepared for future MFA implementation.

**Impact:** MFA cannot be enabled or used.

**Workaround:** Ignore MFA fields until endpoints are implemented.

**Status:** Open — future feature

---

## Patterns to Avoid

### Do Not Put Business Logic in Endpoints

**Mistake:** Adding validation, calculations, or DB queries directly in `app/api/v1/endpoints/`.

**Why it fails:** Breaks testability, duplicates logic, bypasses audit logging.

**Correct approach:** Delegate to service layer via dependency injection.

---

### Do Not Commit in Repositories

**Mistake:** Calling `session.commit()` inside a repository method.

**Why it fails:** Breaks transaction boundaries. Service may need multiple repo operations in one transaction.

**Correct approach:** Let `UnitOfWork` handle commit/rollback.

---

### Do Not Use PUT for Updates

**Mistake:** Creating PUT endpoints for full resource replacement.

**Why it fails:** Risks overwriting fields unintentionally. Conflicts with RLS partial evaluation.

**Correct approach:** PATCH with optional fields in update schemas.

---

### Do Not Store Raw JWT Tokens

**Mistake:** Persisting full access/refresh tokens in the database.

**Why it fails:** Security risk if DB is compromised. No standard revocation mechanism.

**Correct approach:** Store JTI only. Validate JTI on each request.

---

### Do Not Skip Tenant Context

**Mistake:** Making DB queries without tenant middleware setting `app.current_tenant_id`.

**Why it fails:** RLS policies block all rows (strict) or leak cross-tenant data (permissive).

**Correct approach:** Ensure `TenantMiddleware` runs and JWT/header provides tenant_id.

---

## How to Record New Mistakes

When fixing a bug or discovering a gotcha, add an entry:

```markdown
### [Short Title]

**Problem:** What went wrong
**Cause:** Why it happened
**Fix:** How it was resolved
**Status:** Resolved | Open
**Prevention:** How to avoid in future
```

Then update `master-memory.md` if the issue is critical enough for compressed memory.

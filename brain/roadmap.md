# Roadmap — Insight Forge V2

> Future direction, planned work, and product milestones.
> Last updated: 2026-07-10

## Current Phase: Phase 1 — Persistent Project Memory

**Status:** In progress (Project Brain bootstrap)

Establishing the persistent intelligence layer so AI agents can work efficiently without repeated repository analysis.

**Deliverables:**
- [x] `brain/` knowledge system with all core files
- [x] `AGENTS.md` agent workflow definitions
- [x] `workflows/` process templates
- [ ] Memory Agent integration into development workflow
- [ ] Automated brain updates after task completion

---

## Phase 2 — Frontend & Auth Integration

**Priority:** High
**Status:** Complete (Ingress, session controls, zero-trust rendering, and admin monitoring console integrated)

### Frontend Auth Flow
- [x] Login page with corporate email + password
- [x] Token storage and refresh logic
- [x] Protected routes
- [x] Role-based UI rendering (in dashboard header)

### Frontend Dashboards
- [ ] Institutional analytics dashboard
- [ ] Student risk overview
- [ ] Cohort performance views
- [ ] AI pipeline results viewer

### Fix Mock Auth
- [x] Replace `Bearer mock-session-token-admin` in `page.tsx`
- [x] Wire real JWT flow end-to-end

**Key files to create/modify:**
- `insight-forge-frontend/src/app/login/page.tsx`
- `insight-forge-frontend/src/app/dashboard/page.tsx`
- `insight-forge-frontend/src/lib/api.ts` (API client with auth)

---

## Phase 3 — Real LLM Integration

**Priority:** High
**Status:** Not started

### LLM Provider Implementations
- OpenAI provider (`app/ai/llm/openai.py`)
- Anthropic provider (`app/ai/llm/anthropic.py`)
- Provider selection via config (`LLM_PROVIDER` env var)

### Enhanced AI Pipeline
- Streaming responses
- Error recovery between agents
- Cost tracking per pipeline run

**Key files:**
- `app/ai/llm/openai.py` (new)
- `app/core/config.py` (LLM config)
- `app/services/ai_service.py` (provider selection)

---

## Phase 4 — Data Ingestion & Reports

**Priority:** Medium
**Status:** Placeholder routers exist

### Dataset Management
- `POST /api/v1/datasets` — upload and register datasets
- `GET /api/v1/datasets` — list tenant datasets
- Dataset versioning and metadata

### Data Ingestion Pipeline
- `POST /api/v1/ingestion/import` — bulk CSV/JSON import
- Validation and transformation rules
- Progress tracking for large imports

### Reports API
- `GET /api/v1/reports` — list generated reports
- `GET /api/v1/reports/{id}` — download report
- Scheduled report generation

**Key files:**
- `app/api/v1/endpoints/datasets.py` (implement)
- `app/api/v1/endpoints/ingestion.py` (implement)
- `app/api/v1/endpoints/reports.py` (implement)
- New services: `DatasetService`, `IngestionService`, `ReportService`

---

## Phase 5 — Bulk Operations & Performance

**Priority:** Medium
**Status:** TODO comments in code

### Bulk Endpoints
- `POST /api/v1/users/bulk` — bulk user creation
- `POST /api/v1/metrics/bulk` — bulk metric import
- `POST /api/v1/interventions/bulk` — bulk intervention import

### Performance
- Cursor-based pagination (replace offset/limit)
- Redis caching layer for analytics queries
- Query optimization and indexing review

### Rate Limiting
- Per-tenant rate limits
- Per-endpoint throttling

**Key files:**
- `app/api/v1/endpoints/users.py` (bulk endpoint)
- `app/api/v1/endpoints/metrics.py` (bulk endpoint)
- New: `app/core/cache.py` (Redis integration)

---

## Phase 6 — Observability & Security Hardening

**Priority:** Medium
**Status:** Hooks documented, not implemented

### Observability
- OpenTelemetry integration
- Prometheus metrics endpoint
- Structured logging with correlation IDs
- Swappable AuditLogger for external sinks

### Security
- RS256 JWT with key files (production)
- MFA endpoints (TOTP flow)
- Rate limiting
- Request correlation middleware

### Real-Time
- WebSocket support for domain events
- Live dashboard updates

**Key files:**
- `app/main.py` (integration hooks)
- `app/core/security/` (RS256, MFA)
- New: `app/middleware/rate_limit.py`

---

## Phase 7 — Multi-Agent Coordination (Project Brain Phase 2)

**Priority:** Low (future)
**Status:** Vision only

- Automated Architect → Developer → Reviewer → QA → Memory agent pipeline
- Task artifacts in `workflows/artifacts/`
- Agent handoff protocols
- Quality gates between agent stages

---

## Phase 8 — Autonomous Improvement

**Priority:** Low (future)
**Status:** Vision only

- Automatic knowledge extraction from code changes
- Self-improving documentation
- Refactoring suggestions based on pattern drift
- Security analysis automation
- Benchmark tracking over time

---

## Completed Milestones

| Milestone | Date | Notes |
|-----------|------|-------|
| Database layer + RLS | ✅ | Initial schema migration |
| Repository layer | ✅ | BaseRepository + entity repos |
| Service layer | ✅ | All domain services |
| Authentication | ✅ | JWT + sessions + RBAC |
| API endpoints | ✅ | All core CRUD + analytics + AI + cleaning |
| AI multi-agent pipeline | ✅ | 4 agents + orchestrator (mock LLM) |
| Data cleaning pipeline | ✅ | CSV/XLSX processing |
| Unit test suite | ✅ | 22 test files |
| Architecture docs | ✅ | 9 docs in docs/architecture/ |
| Docker Compose | ✅ | Full stack orchestration |
| Project Brain bootstrap | ✅ | brain/ + AGENTS.md + workflows/ |

---

## Technical Debt

| Item | Priority | Notes |
|------|----------|-------|
| Update backend README checklist | Low | Shows incomplete but code is done |
| Fix docker-compose DATABASE_URL driver | Medium | asyncpg → plain postgresql:// |
| Align JWT algorithm docs | Low | README vs config.py mismatch |
| requirements.txt completeness | Low | Only 5 packages; full deps in pyproject.toml |
| Add monorepo root README | Low | Only backend README exists |

---

## How to Update This Roadmap

After completing work:
1. Move item from planned → completed milestones
2. Update status in phase sections
3. Add new phases/items as discovered
4. Update `master-memory.md` roadmap snapshot
5. Update `memory.md` active work section

# Dependency Graph — Insight Forge V2

> How layers and modules connect. Use to understand impact of changes.
> Last updated: 2026-07-10

## High-Level Request Flow

```
Client (Browser / API Consumer)
    │
    ▼
┌─────────────────────────────────────────┐
│           Middleware Stack               │
│  TrustedHost → CORS → GZip → RequestID  │
│  → SecurityHeaders → Timing → Tenant    │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│         API Layer (endpoints/)           │
│  Validation → RBAC → Delegate to Service │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│         Service Layer (services/)        │
│  Business Logic → UoW → Audit Logging   │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│      Repository Layer (repositories/)     │
│  Stateless CRUD → SQLAlchemy Queries    │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│    Database (PostgreSQL + RLS)           │
│  SET LOCAL app.current_tenant_id        │
└─────────────────────────────────────────┘
```

## Frontend → Backend

```
insight-forge-frontend/src/app/page.tsx
    │ POST /api/v1/ai/analyze (multipart file upload)
    │ Authorization: Bearer <token>
    ▼
insight-forge-backend/app/api/v1/endpoints/ai.py
    ▼
insight-forge-backend/app/services/ai_service.py
    ▼
insight-forge-backend/app/ai/orchestration/orchestrator.py
    ▼
insight-forge-backend/app/ai/agents/*.py
    ▼
insight-forge-backend/app/ai/llm/provider.py
```

## Authentication Dependency Chain

```
Request with Authorization header
    ▼
TenantMiddleware (app/middleware/tenant.py)
    │ extracts tenant_id from JWT or X-Tenant-ID
    ▼
get_current_session (app/dependencies/auth.py)
    │ validates JWT signature, type=access
    │ checks JTI exists in DB
    ▼
SessionRepository → sessions table (RLS)
    ▼
get_current_user (app/dependencies/auth.py)
    │ loads user from session.sub
    ▼
UserRepository → users table (RLS)
    ▼
RequireRoles (app/dependencies/auth.py)
    │ checks user.role against required roles
    ▼
Endpoint handler executes
```

## Service Dependency Injection

```
FastAPI Depends(get_*_service)
    ▼
app/dependencies/services.py
    │ creates ServiceContext
    ▼
ServiceContext
    ├── get_async_session()     → app/db/session.py
    ├── UnitOfWork              → app/services/uow.py
    ├── AuditLogger             → app/services/audit.py
    ├── ClockProvider           → app/services/providers.py
    └── UUIDProvider            → app/services/providers.py
    ▼
Service instance (e.g., UserService)
    ├── _repo: UserRepository   → app/repositories/user.py
    ├── _uow: UnitOfWork
    └── _audit: AuditLogger
```

## Database Connection Chain

```
app/core/config.py
    │ DATABASE_URL → async_database_url (psycopg rewrite)
    ▼
app/db/engine.py
    │ create_async_engine with pool settings
    ▼
app/db/session.py
    │ get_async_session() → AsyncSession
    │ injects SET LOCAL app.current_tenant_id
    ▼
app/db/tenant_context.py
    │ ContextVar[current_tenant_id]
    │ set by TenantMiddleware
    ▼
app/repositories/*.py
    │ SQLAlchemy queries (RLS auto-filters)
    ▼
PostgreSQL tables
```

## AI Pipeline Internal Graph

```
AIService (app/services/ai_service.py)
    │
    ├── File parsing (CSV/JSON)
    ├── AIContext creation
    │
    ▼
AIWorkflowOrchestrator (app/ai/orchestration/orchestrator.py)
    │
    ├── AIDataEngineer (app/ai/agents/data_engineer.py)
    │   ├── AIContext.evolve(stage="data_engineering")
    │   └── BaseLLMProvider.generate()
    │
    ├── AIDataAnalyst (app/ai/agents/data_analyst.py)
    │   ├── AIContext.evolve(stage="data_analysis")
    │   └── BaseLLMProvider.generate()
    │
    ├── AIBusinessAnalyst (app/ai/agents/business_analyst.py)
    │   ├── AIContext.evolve(stage="business_analysis")
    │   └── BaseLLMProvider.generate()
    │
    └── AIExecutiveReportGenerator (app/ai/agents/executive_report.py)
        ├── AIContext.evolve(stage="executive_report")
        └── BaseLLMProvider.generate()
    │
    ▼
OrchestratedPipelineResult
    ├── consolidated_report
    ├── per_agent_metrics (timing)
    └── warnings
```

## Analytics Data Flow

```
GET /api/v1/analytics/*
    ▼
AnalyticsService (app/services/analytics.py)
    │
    ├── StudentMetricRepository → student_metrics (RLS)
    ├── CohortRepository → cohorts (RLS)
    ├── CoachingInterventionRepository → coaching_interventions (RLS)
    │
    ├── Risk classification (deterministic rules)
    ├── KPI aggregation
    ├── Health score calculation
    │
    ▼
Analytics response schemas (app/schemas/analytics.py)
    ▼
api_response() envelope
```

## Cleaning Pipeline Graph

```
POST /api/v1/cleaning/analyze
    ▼
CleaningService (app/services/cleaning.py)
    ▼
CleaningPipeline (app/pipelines/cleaning_pipeline.py)
    │
    ├── app/ai/utils/cleaning.py (cleaning utilities)
    ├── app/ai/utils/profiler.py (data profiling)
    │
    ▼
TrustedDataset output
    ├── quality_score
    ├── audit_log
    └── cleaned_data
```

## Module Import Dependencies

```
app/main.py
    ├── app/lifespan.py
    ├── app/api/v1/router.py
    │   └── app/api/v1/endpoints/*.py
    │       └── app/dependencies/services.py
    │           └── app/services/*.py
    │               ├── app/repositories/*.py
    │               ├── app/services/uow.py
    │               └── app/services/audit.py
    ├── app/middleware/*.py
    └── app/core/config.py
        └── app/db/engine.py
            └── app/db/session.py
```

## External Dependencies

| Dependency | Used By | Status |
|------------|---------|--------|
| PostgreSQL 16 | All data operations | Active |
| Redis 7 | Configured, not integrated | Pending |
| Celery | Configured, stub only | Pending |
| LLM APIs (OpenAI, etc.) | AI agents via BaseLLMProvider | Mock only |
| Neon PostgreSQL | Production target | Configured |

## Change Impact Guide

| If you change... | Also check... |
|------------------|---------------|
| `app/models/*.py` | Migration, repositories, API schemas, RLS policies |
| `app/services/*.py` | Repositories, tests, API endpoints |
| `app/api/v1/endpoints/*.py` | Service methods, auth guards, response schemas |
| `app/core/config.py` | docker-compose.yml, .env.example, README |
| `app/middleware/tenant.py` | All tenant-scoped queries, RLS policies |
| `app/ai/agents/*.py` | Orchestrator, AIContext, LLM provider, tests |
| `migrations/` | Models, repositories, seed scripts |

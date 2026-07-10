# Feature Map — Insight Forge V2

> Maps features to implementation files. Use to locate code quickly.
> Last updated: 2026-07-10

## Authentication & Authorization

| Feature | Status | Files |
|---------|--------|-------|
| Login (email + password) | ✅ | `endpoints/auth.py`, `services/auth.py` |
| JWT access token (15 min) | ✅ | `core/security/jwt.py`, `services/session.py` |
| JWT refresh token (7 days) | ✅ | `endpoints/auth.py`, `services/auth.py` |
| Token rotation | ✅ | `services/session.py`, `docs/architecture/authentication.md` |
| Logout (single session) | ✅ | `endpoints/auth.py`, `services/auth.py` |
| Logout all sessions | ✅ | `endpoints/auth.py`, `services/auth.py` |
| Current user (me) | ✅ | `endpoints/auth.py` |
| RBAC (role enforcement) | ✅ | `dependencies/auth.py`, `core/roles.py` |
| Tenant middleware | ✅ | `middleware/tenant.py`, `db/tenant_context.py` |
| MFA | ❌ | Fields in `models/user.py` only; no endpoints |

## Tenant Management

| Feature | Status | Files |
|---------|--------|-------|
| Create tenant | ✅ | `endpoints/tenants.py`, `services/tenant.py`, `repositories/tenant.py`, `models/tenant.py` |
| List tenants | ✅ | `endpoints/tenants.py`, `services/tenant.py` |
| Get tenant by ID | ✅ | `endpoints/tenants.py`, `services/tenant.py` |
| Update tenant | ✅ | `endpoints/tenants.py`, `services/tenant.py` |
| Delete tenant | ✅ | `endpoints/tenants.py`, `services/tenant.py` |

## User Management

| Feature | Status | Files |
|---------|--------|-------|
| Create user | ✅ | `endpoints/users.py`, `services/user.py`, `repositories/user.py`, `models/user.py` |
| List users | ✅ | `endpoints/users.py`, `services/user.py` |
| Get user by ID | ✅ | `endpoints/users.py`, `services/user.py` |
| Update user (PATCH) | ✅ | `endpoints/users.py`, `services/user.py` |
| Delete user | ✅ | `endpoints/users.py`, `services/user.py` |
| Password hashing | ✅ | `core/security/passwords.py` |
| Bulk user import | ❌ | TODO comment in `endpoints/users.py` |

## Cohort Management

| Feature | Status | Files |
|---------|--------|-------|
| Create cohort | ✅ | `endpoints/cohorts.py`, `services/cohort.py`, `repositories/cohort.py`, `models/cohort.py` |
| List cohorts | ✅ | `endpoints/cohorts.py`, `services/cohort.py` |
| Get cohort by ID | ✅ | `endpoints/cohorts.py`, `services/cohort.py` |
| Update cohort (PATCH) | ✅ | `endpoints/cohorts.py`, `services/cohort.py` |
| Delete cohort | ✅ | `endpoints/cohorts.py`, `services/cohort.py` |

## Student Metrics

| Feature | Status | Files |
|---------|--------|-------|
| Create metric | ✅ | `endpoints/metrics.py`, `services/student_metric.py`, `repositories/student_metric.py`, `models/student_metric.py` |
| List metrics | ✅ | `endpoints/metrics.py`, `services/student_metric.py` |
| Get metric by ID | ✅ | `endpoints/metrics.py`, `services/student_metric.py` |
| Update metric (PATCH) | ✅ | `endpoints/metrics.py`, `services/student_metric.py` |
| Delete metric | ✅ | `endpoints/metrics.py`, `services/student_metric.py` |
| Risk status field | ✅ | `models/student_metric.py` (Safe/Amber/Critical) |

## Coaching Interventions

| Feature | Status | Files |
|---------|--------|-------|
| Create intervention | ✅ | `endpoints/interventions.py`, `services/coaching_intervention.py`, `repositories/coaching_intervention.py`, `models/coaching_intervention.py` |
| List interventions | ✅ | `endpoints/interventions.py`, `services/coaching_intervention.py` |
| Get intervention by ID | ✅ | `endpoints/interventions.py`, `services/coaching_intervention.py` |
| Update intervention (PATCH) | ✅ | `endpoints/interventions.py`, `services/coaching_intervention.py` |
| Delete intervention | ✅ | `endpoints/interventions.py`, `services/coaching_intervention.py` |
| Encrypted notes | ✅ | `db/types/encrypted.py`, `models/coaching_intervention.py` |
| Bulk intervention import | ❌ | TODO comment in `endpoints/interventions.py` |

## Academic Analytics

| Feature | Status | Files |
|---------|--------|-------|
| Dashboard | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| KPIs | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Student risk view | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Cohort performance | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Faculty performance | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Institution overview | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Trends | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Recommendations | ✅ | `endpoints/analytics.py`, `services/analytics.py` |
| Risk classification rules | ✅ | `docs/architecture/analytics.md`, `services/analytics.py` |
| Health score | ✅ | `services/analytics.py` |
| Analytics schemas | ✅ | `schemas/analytics.py` |

## AI Multi-Agent Pipeline

| Feature | Status | Files |
|---------|--------|-------|
| File upload endpoint | ✅ | `endpoints/ai.py` |
| AI service orchestration | ✅ | `services/ai_service.py` |
| Workflow orchestrator | ✅ | `ai/orchestration/orchestrator.py` |
| Data Engineer agent | ✅ | `ai/agents/data_engineer.py` |
| Data Analyst agent | ✅ | `ai/agents/data_analyst.py` |
| Business Analyst agent | ✅ | `ai/agents/business_analyst.py` |
| Executive Report agent | ✅ | `ai/agents/executive_report.py` |
| AI context model | ✅ | `ai/context/model.py` |
| Agent contract | ✅ | `ai/contracts/agent.py` |
| LLM provider abstraction | ✅ | `ai/llm/provider.py` |
| Default (mock) LLM | ✅ | `ai/llm/default.py` |
| Real LLM providers | ❌ | Interface exists; no implementations |

## Data Cleaning

| Feature | Status | Files |
|---------|--------|-------|
| File upload endpoint | ✅ | `endpoints/cleaning.py` |
| Cleaning service | ✅ | `services/cleaning.py` |
| Cleaning pipeline | ✅ | `pipelines/cleaning_pipeline.py` |
| Cleaning utilities | ✅ | `ai/utils/cleaning.py` |
| Data profiler | ✅ | `ai/utils/profiler.py` |

## Infrastructure

| Feature | Status | Files |
|---------|--------|-------|
| Health check | ✅ | `endpoints/health.py`, `app/main.py` |
| Docker Compose | ✅ | `docker-compose.yml` |
| Alembic migrations | ✅ | `migrations/versions/9092070a0ca7_initial_schema.py` |
| Windows dev server | ✅ | `serve.py` |
| Bootstrap script | ✅ | `scripts/bootstrap.py` |
| Seed database | ✅ | `scripts/seed_database.py` |
| Verify scripts | ✅ | `scripts/verify_*.py` |
| Redis integration | ❌ | Config in docker-compose only |
| Celery workers | ❌ | `workers/tasks/analytics.py` (stub) |
| Background analytics | ❌ | `pipelines/analytics_pipeline.py` (stub) |

## Frontend

| Feature | Status | Files |
|---------|--------|-------|
| AI upload dashboard | ✅ | `frontend/src/app/page.tsx` |
| Root layout | ✅ | `frontend/src/app/layout.tsx` |
| Global styles | ✅ | `frontend/src/app/globals.css` |
| Auth flow | ❌ | Not implemented |
| Analytics dashboards | ❌ | Not implemented |
| Admin UI | ❌ | Not implemented |

## Placeholder Features

| Feature | Status | Files |
|---------|--------|-------|
| Dataset management | ❌ | `endpoints/datasets.py` (router only) |
| Data ingestion | ❌ | `endpoints/ingestion.py` (router only) |
| Reports | ❌ | `endpoints/reports.py` (router only) |

## Test Coverage

| Area | Test File |
|------|-----------|
| Auth | `tests/unit/test_auth.py` |
| API endpoints | `tests/unit/test_api_endpoints.py` |
| Services | `tests/unit/test_services.py` |
| Repositories | `tests/unit/test_repositories.py` |
| Analytics | `tests/unit/test_analytics.py` |
| AI foundation | `tests/unit/test_ai_foundation.py` |
| AI API | `tests/unit/test_ai_api.py` |
| Cleaning API | `tests/unit/test_cleaning_api.py` |
| Orchestrator | `tests/unit/test_orchestrator.py` |
| Data agents | `tests/unit/test_data_engineer.py`, `test_data_analyst.py`, `test_business_analyst.py` |
| Executive report | `tests/unit/test_executive_report.py` |
| Docker setup | `tests/integration/test_docker_setup.py` |

# Glossary — Insight Forge V2

> Project terminology. Use these definitions consistently.
> Last updated: 2026-07-10

## Core Domain Terms

### Tenant
An institutional partner — the top-level organizational partition. Each tenant represents a university, college, or educational institution using the platform. Identified by UUID `tenant_id`. The `tenants` table is global (no RLS) since tenant records are managed at platform level.

### User
A person within a tenant scope. Has a `corporate_email` (login identifier), `role` (Admin/Dean/Faculty/Student), and belongs to exactly one tenant. Tenant-scoped via RLS.

### Cohort
A group of students within a tenant, identified by `cohort_code` and `department_scope`. Used to organize students for analytics and intervention tracking. Tenant-scoped via RLS.

### Student Metric
An academic record for a student within a cohort. Contains:
- `raw_average_grade` (GPA)
- `attendance_percentage`
- `success_indicator_status` (Safe / Amber / Critical)

Represents a point-in-time academic snapshot. Tenant-scoped via RLS.

### Coaching Intervention
An advisory action logged by faculty or dean for a student. Contains intervention type, date, and `intervention_notes` (encrypted at rest). Used in risk classification calculations. Tenant-scoped via RLS.

## Risk & Analytics Terms

### Risk Tier / Success Indicator Status
Classification of student academic health:

| Tier | Meaning |
|------|---------|
| **Safe** | GPA ≥ 3.0, attendance ≥ 85%, ≤ 1 intervention |
| **Amber** | Moderate risk — GPA 2.0–3.0 or attendance 70–85% or 2 interventions |
| **Critical** | High risk — GPA < 2.0 or attendance < 70% or ≥ 3 interventions |

Deterministic rules, not ML-based. See `docs/architecture/analytics.md`.

### Health Score
A weighted institutional index calculated from the distribution of risk tiers across all students in a tenant. Higher score = healthier institution.

### KPI (Key Performance Indicator)
Aggregated metrics displayed on analytics dashboards: student counts by risk tier, average GPA, attendance rates, intervention frequency.

## Authentication Terms

### Session
A database record tracking an active JWT session. Contains `jti` (JWT ID), expiry timestamp, and ingress IP. Not a "user workspace session" — specifically a token lifecycle record. Tenant-scoped via RLS.

### JTI (JWT ID)
A unique identifier claim in JWT tokens. Ties each token to a database session record. Used for revocation (logout), rotation (refresh), and reuse detection.

### Corporate Email
The user's login identifier (`corporate_email` column). Institution-assigned email address used for authentication.

### Role
User permission level: `Admin`, `Dean`, `Faculty`, `Student`. Enforced via `RequireRoles` dependency on API endpoints.

## Technical Terms

### RLS (Row-Level Security)
PostgreSQL feature enforcing tenant isolation at the database level. Uses session variable `app.current_tenant_id` set per request. Policies on tenant-scoped tables filter rows automatically.

### ServiceResult
Wrapper returned by service commands: `{success, entity, message, errors}`. Endpoints translate this to API response envelope.

### UnitOfWork (UoW)
Transaction boundary in the service layer. `async with uow` auto-commits on success, auto-rolls back on exception.

### ServiceContext
Bundle of dependencies injected into services: database session, UoW, audit logger, clock provider, UUID provider.

### API Response Envelope
Standard JSON response shape: `{success, message, data, meta, errors}`. All endpoints use `api_response()` helper.

### EncryptedString
Custom SQLAlchemy column type that encrypts values at the application level before storing in PostgreSQL. Used for `totp_secret` and `intervention_notes`.

## AI Pipeline Terms

### Agent
An AI pipeline stage implementing the `BaseAIAgent` contract. Each agent performs a specific analysis task and evolves the shared context.

### AIContext
Immutable shared state object passed between agents in the pipeline. Contains uploaded data, analysis results, and metadata. Evolved via `context.evolve()` — never mutated directly.

### Orchestrator
`AIWorkflowOrchestrator` — manages sequential execution of agents, collects per-agent timing metrics, and produces the final `OrchestratedPipelineResult`.

### LLM Provider
Abstraction over language model APIs. `BaseLLMProvider` interface with `DefaultLLMProvider` (mock) as default implementation.

### Trusted Dataset
Output of the data cleaning pipeline. A validated, quality-scored dataset with an audit log of transformations applied.

### Consolidated Report
Final output of the AI pipeline — executive summary combining insights from all agents.

## Infrastructure Terms

### Workspace
Informal term for a tenant's operational scope. Used in AI context (`AIContext.tenant_id` described as "active tenant workspace"). **Not a separate database entity.**

### Neon
Serverless PostgreSQL provider targeted for production deployment. Connection via `DATABASE_URL` with SSL.

### SelectorEventLoop
Windows-compatible asyncio event loop policy required for psycopg3. Set via `serve.py` or `app/main.py` lifespan.

## Abbreviations

| Abbreviation | Full Term |
|-------------|-----------|
| RLS | Row-Level Security |
| JTI | JWT ID |
| UoW | Unit of Work |
| RBAC | Role-Based Access Control |
| MFA | Multi-Factor Authentication |
| BI | Business Intelligence |
| KPI | Key Performance Indicator |
| GPA | Grade Point Average |
| DTO | Data Transfer Object |
| DI | Dependency Injection |

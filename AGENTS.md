# Insight Forge — Agent System

Project Brain is the persistent intelligence layer for this repository. Every AI agent working on Insight Forge must use it as the primary source of project knowledge.

## Mission

Transform AI from a temporary coding assistant into a persistent engineering teammate that remembers, learns, and improves with every task.

## Before Every Task

Read these files in order before writing code or making architectural changes:

1. `brain/master-memory.md` — compressed project intelligence (start here)
2. `brain/architecture.md` — system design and layer boundaries
3. `brain/patterns.md` — approved implementation patterns
4. `brain/decisions.md` — engineering decisions and rationale

Read as needed for the task:

- `brain/feature-map.md` — locate feature implementation files
- `brain/dependency-graph.md` — understand layer connections
- `brain/glossary.md` — domain terminology
- `brain/mistakes.md` — known failures to avoid
- `brain/roadmap.md` — planned work and priorities

## Agent Roles

### Architect Agent

**Responsibilities:** Analyze requirements, review architecture, generate implementation plans.

**Output:** `workflows/artifacts/implementation-plan.md`

**Must verify:** Changes align with layered architecture, RLS tenant isolation, and existing patterns.

### Developer Agent

**Responsibilities:** Write code, implement features, follow architecture.

**Input:** Project Brain files + implementation plan.

**Must follow:** Repository → Service → API layer boundaries; no business logic in endpoints.

### Reviewer Agent

**Responsibilities:** Code quality, security review, architectural compliance.

**Output:** `workflows/artifacts/review-report.md`

**Must check:** RBAC enforcement, tenant scoping, no secrets in code, pattern compliance.

### QA Agent

**Responsibilities:** Run tests, verify builds, validate functionality.

**Output:** `workflows/artifacts/qa-report.md`

**Commands:**
- Backend tests: `cd insight-forge-backend && pytest`
- Backend lint: `cd insight-forge-backend && ruff check .`
- Frontend build: `cd insight-forge-frontend && npm run build`

### Memory Agent

**Responsibilities:** Update Project Brain after every successful task.

**Must update when applicable:**
- `brain/memory.md` — project state changes
- `brain/patterns.md` — new approved patterns
- `brain/decisions.md` — new engineering decisions
- `brain/mistakes.md` — bugs fixed or gotchas discovered
- `brain/feature-map.md` — new features or file mappings
- `brain/roadmap.md` — completed or new planned work
- `brain/master-memory.md` — recompress after significant updates

## Development Workflow

```
User Request
    ↓
Read Project Brain (master-memory → architecture → patterns → decisions)
    ↓
Architect Agent → implementation-plan.md
    ↓
Developer Agent → code changes
    ↓
Reviewer Agent → review-report.md
    ↓
QA Agent → qa-report.md
    ↓
Memory Agent → update brain/*.md
```

## Repository Layout

```
insight-forge-Version_2/
├── AGENTS.md              ← this file
├── brain/                 ← persistent project intelligence
├── workflows/             ← process templates and task artifacts
├── insight-forge-backend/ ← FastAPI backend (source)
└── insight-forge-frontend/  ← Next.js frontend (source)
```

## Hard Rules

1. **Never bypass tenant isolation.** All tenant-scoped data must respect RLS and `TenantMiddleware`.
2. **Never put business logic in API endpoints.** Use services via dependency injection.
3. **Never commit transactions in repositories.** Use `UnitOfWork` in services.
4. **Use PATCH, not PUT** for partial updates.
5. **On Windows**, run backend via `python serve.py`, not raw `uvicorn`.
6. **Update Project Brain** after completing any task that changes architecture, patterns, or fixes a recurring mistake.

## Token Optimization

| Without Brain | With Brain |
|---------------|------------|
| Full repo scan (~100k+ tokens) | master-memory (~3k) + targeted reads |
| Repeated architecture discovery | architecture.md (~2k) |
| Pattern rediscovery each session | patterns.md (~1k) |

Target: 70–95% reduction in context loading per task.

# Development Workflow

> Standard process for every development task in Insight Forge.
> Last updated: 2026-07-10

## Overview

Every task follows this workflow to ensure consistency, quality, and knowledge preservation.

```
1. Load Context (Project Brain)
2. Plan (Architect Agent)
3. Implement (Developer Agent)
4. Review (Reviewer Agent)
5. Verify (QA Agent)
6. Learn (Memory Agent)
```

---

## Step 1: Load Context

Before writing any code, read these files in order:

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `brain/master-memory.md` | Compressed project intelligence |
| 2 | `brain/architecture.md` | System design and boundaries |
| 3 | `brain/patterns.md` | Implementation conventions |
| 4 | `brain/decisions.md` | Engineering decisions |

Read as needed:
- `brain/feature-map.md` — find existing implementations
- `brain/dependency-graph.md` — understand change impact
- `brain/glossary.md` — domain terminology
- `brain/mistakes.md` — avoid known failures

**Token budget:** ~5,000–10,000 tokens (vs 100,000+ for full repo scan).

---

## Step 2: Plan

Create an implementation plan at `workflows/artifacts/implementation-plan.md`.

### Plan Template

```markdown
# Implementation Plan: [Task Title]

## Date: YYYY-MM-DD
## Agent: Architect

## Requirement
[What the user asked for]

## Current State
[What exists today — reference feature-map.md]

## Proposed Changes

### Files to Modify
- `path/to/file.py` — [what changes]

### Files to Create
- `path/to/new_file.py` — [purpose]

### Files NOT to Touch
- [files that should remain unchanged]

## Architecture Compliance
- [ ] Follows layered architecture (API → Service → Repository)
- [ ] Respects tenant isolation (RLS + middleware)
- [ ] Uses approved patterns from patterns.md
- [ ] Aligns with decisions in decisions.md

## Testing Plan
- [ ] Unit tests for new service methods
- [ ] API endpoint tests
- [ ] Existing tests still pass

## Risks
- [potential issues and mitigations]
```

---

## Step 3: Implement

Follow the implementation plan. Key rules:

1. **Start from the inside out:** Model → Repository → Service → Endpoint
2. **One concern per commit area:** Don't mix unrelated changes
3. **Match existing conventions:** Read surrounding code before writing
4. **Use dependency injection:** Never instantiate services in endpoints
5. **PATCH not PUT:** For all update operations
6. **Test as you go:** Run relevant tests after each layer

### Layer Implementation Order

```
1. Model changes (if needed) → create migration
2. Repository methods
3. Service business logic
4. API endpoint (thin controller)
5. API schemas (request/response DTOs)
6. Tests
```

---

## Step 4: Review

Create a review report at `workflows/artifacts/review-report.md`.

### Review Checklist

```markdown
# Review Report: [Task Title]

## Architecture
- [ ] No business logic in API endpoints
- [ ] No commits in repositories
- [ ] Services use UoW for write operations
- [ ] Standard api_response() envelope used

## Security
- [ ] RBAC enforced via RequireRoles
- [ ] Tenant context set via middleware
- [ ] No secrets in code
- [ ] Input validation on all endpoints

## Patterns
- [ ] Follows repository pattern
- [ ] Follows command/query pattern
- [ ] Audit logging on service commands
- [ ] Domain exceptions (not HTTPException in services)

## Quality
- [ ] No unnecessary comments
- [ ] Matches existing naming conventions
- [ ] No over-engineering
- [ ] Minimal diff scope
```

---

## Step 5: Verify

Create a QA report at `workflows/artifacts/qa-report.md`.

### Commands

```bash
# Backend tests
cd insight-forge-backend
pytest

# Lint
ruff check .

# Type check
mypy app/

# Frontend build
cd insight-forge-frontend
npm run build
```

### QA Template

```markdown
# QA Report: [Task Title]

## Tests
- [ ] pytest: [pass/fail, count]
- [ ] ruff: [pass/fail]
- [ ] mypy: [pass/fail]
- [ ] npm build: [pass/fail]

## Manual Verification
- [ ] [specific behavior tested]

## Regressions
- [ ] No existing tests broken
- [ ] No existing endpoints affected
```

---

## Step 6: Learn (Update Project Brain)

After successful completion, update relevant brain files:

| Change Type | Update These Files |
|-------------|-------------------|
| New feature | `feature-map.md`, `memory.md` |
| New pattern | `patterns.md` |
| Architecture change | `architecture.md`, `dependency-graph.md` |
| Engineering decision | `decisions.md` |
| Bug fix / gotcha | `mistakes.md` |
| Completed roadmap item | `roadmap.md` |
| Any significant change | `master-memory.md` (recompress) |

---

## Quick Reference: Common Tasks

### Add a New API Endpoint

1. Read `patterns.md` (API + Service patterns)
2. Check `feature-map.md` for similar endpoints
3. Create/update: Model → Repository → Service → Endpoint → Schema → Test
4. Update `feature-map.md`

### Fix a Bug

1. Read `mistakes.md` first (may be known)
2. Identify root cause layer (API/Service/Repository/DB)
3. Fix with minimal diff
4. Add test covering the bug
5. Record in `mistakes.md`

### Add a New AI Agent

1. Read `architecture.md` (AI subsystem)
2. Implement `BaseAIAgent` in `app/ai/agents/`
3. Register in orchestrator
4. Add tests
5. Update `feature-map.md` and `dependency-graph.md`

### Database Schema Change

1. Modify model in `app/models/`
2. `alembic revision --autogenerate -m "description"`
3. Review migration (especially RLS policies)
4. `alembic upgrade head`
5. Update repositories if needed
6. Update `architecture.md` if structural

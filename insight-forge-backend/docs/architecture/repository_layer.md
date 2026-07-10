# Repository Layer Specification — Insight Forge V2

This document describes the design, API, and constraints of the Repository Layer.

---

## 1. Design & Abstraction

All data access is mediated by the **Repository Pattern** to completely isolate the persistence layer from the business service layer.

- **Abstract Generic**: `BaseRepository[ModelType]` provides type-safe CRUD operations.
- **Dependency Injection**: Repositories are stateless and accept an `AsyncSession` constructor injection.
- **Transaction Exclusions**: Repositories do **not** invoke `session.commit()` or `session.rollback()`. Changes are flushed (`session.flush()`) and committed by the Service Layer.

---

## 2. API Contract

The base interface provides standard queries:
- `create(entity)`: Adds entity to the session.
- `get_by_id(id_)`: Fetches a single instance by primary key.
- `get_one_or_none(**filters)`: Fetches a single instance using keyword filters.
- `get_all(limit, offset, order_by, **filters)`: Fetches list matching filters.
- `paginate(limit, offset, order_by, **filters)`: Fetches paginated subset and row count.
- `update(entity, **updates)`: Updates fields dynamically on loaded instance.
- `delete(entity)`: Performs physical session deletion.
- `exists(**filters)`: Performs lightweight existence verification.
- `count(**filters)`: Counts matching rows.

---

## 3. Entity Mappings

Repositories are implemented only for active database tables:
- **TenantRepository**: URL slug mappings and existence validation.
- **UserRepository**: Lookup by email, existence queries, and role list filters.
- **SessionRepository**: Lookup by JTI and recent session history.
- **CohortRepository**: Lookup by tenant and cohort code.
- **StudentMetricRepository**: Retrieval of academic/attendance telemetry.
- **CoachingInterventionRepository**: Logging and retrieval of advisory intervention events.

---

## 4. Query Guidelines

- Avoid loading unnecessary rows (prefer `exists()` over full counts or selects).
- Standardize sorting parameters to prevent runtime query failures.
- Eager relationships (`joinedload` / `selectinload`) should be explicitly invoked only when N+1 query scans occur.

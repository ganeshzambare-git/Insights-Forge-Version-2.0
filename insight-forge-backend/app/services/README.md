# Service Layer Architecture Guide — Insight Forge V2

This package implements the Service/Business Layer of **Insight Forge V2**. It manages domain rule validations, transaction orchestration (via Unit of Work), and audit logging.

---

## 1. Request Execution Lifecycle

Every command request flows through the architectural boundaries in a strict linear sequence:

```
[API / Route]
     │
     ▼
[Dependency Factories] ──► (Inject repositories, UnitOfWork, context, clock, and audit logger)
     │
     ▼
[Domain Service] ────► 1. Trigger Audit Start
     │                 2. Input & Business Validations
     │                 3. Repository Reads
     │                 4. Business Logic execution
     │                 5. Repository Writes
     │                 6. session.flush()
     │                 7. UnitOfWork.__aexit__ (triggers session.commit())
     │                 8. session.refresh()
     │                 9. Trigger Audit Success
     ▼
[Result / DTO]
```

---

## 2. Service-to-Repository Separation (Command vs Query)

To keep boundaries clean, we enforce strict patterns on method signatures:
1. **Commands (Mutations)**: Return `ServiceResult[T]` wrapping transaction success, warning messages, and the affected entity. Always runs inside `execute_command` and handles transaction boundaries.
2. **Queries**: Return direct ORM entities, lists, sequences, or `None`. They do not require a `ServiceResult` wrapper.

---

## 3. Implemented Business Services

- **TenantService**: Governs institutional partition boundaries. Normalizes slugs and validates slug uniqueness before creating tenants.
- **UserService**: Validates roles (`Admin`, `Dean`, `Faculty`, `Student`) and email uniqueness. Receives pre-hashed password strings to keep cryptographic logic decoupled.
- **SessionService**: Controls JTI claims, login tracking, client IP ingress auditing, and automatic tenant-scoped expired session purging.
- **CohortService**: Partitioned class groups. Ensures cohort code uniqueness inside tenant boundaries.
- **StudentMetricService**: Tracks grade averages (validates ranges `0.00` to `100.00`), attendance metrics, and indicator status labels (`Safe`, `Amber`, `Critical`).
- **CoachingInterventionService**: Validates academic intervention workflows (e.g. only advising faculty/deans can record logs for users in student roles).

---

## 4. Repository Constraints (Freeze Rules)

Repositories are strictly data access adapters.

```
Repositories DO NOT contain:
❌ Business Rules
❌ Transactions
❌ Authorization
❌ Validation
❌ Logging

Only query execution and persistence mapping.
```

---

## 5. Domain Validation & Exceptions

- All business policy exceptions must raise structured exceptions from `app.services.exceptions` (e.g. `ValidationError`, `ConflictError`).
- No HTTP exceptions are allowed inside services, preserving decoupling from FastAPI.

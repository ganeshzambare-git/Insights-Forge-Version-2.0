# Schema Intake — `coaching_interventions`

## Module
`interventions`

## Purpose
Records every advisory interaction a faculty member makes for an at-risk student.
Each row is an immutable audit entry capturing who intervened, who was the target
student, when the action occurred, and the (encrypted) notes written by the
advisor. This table is the backbone of the coaching workflow and compliance audit
trail.

---

## Table Definition

### Table Name
`coaching_interventions`

### SQLAlchemy ORM Class Name
`CoachingIntervention`

---

## Columns

| Column                  | PostgreSQL Type            | Nullable | Default                | Constraints                         | Description                                            |
|-------------------------|----------------------------|----------|------------------------|-------------------------------------|--------------------------------------------------------|
| `intervention_id`       | `UUID`                     | NOT NULL | `gen_random_uuid()`    | PRIMARY KEY                         | Unique advisor action record identifier                |
| `tenant_id`             | `UUID`                     | NOT NULL | —                      | FK → `tenants(tenant_id)`          | Tenant row-access marker                               |
| `student_user_id`       | `UUID`                     | NOT NULL | —                      | FK → `users(user_id)`              | Target student being advised                           |
| `faculty_user_id`       | `UUID`                     | NOT NULL | —                      | FK → `users(user_id)`              | Advisor / faculty member logging the intervention      |
| `intervention_notes`    | `TEXT`                     | NOT NULL | —                      |                                     | Encrypted advising context (AES-256 at app layer)      |
| `recorded_timestamp`    | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `CURRENT_TIMESTAMP`    |                                     | UTC timestamp of when the intervention was recorded    |

---

## Primary Key
- `intervention_id` (UUID, server-generated via `gen_random_uuid()`)

## Unique Constraints
None.

## Check Constraints
None explicitly stated.

> **Design note**: Consider a check constraint `student_user_id <> faculty_user_id`
> to prevent a user from logging an intervention against themselves. Defer to
> model-lock decision.

## Foreign Keys
| Constraint Name                               | Column             | References               | On Delete         |
|-----------------------------------------------|--------------------|--------------------------|-------------------|
| `fk_coaching_interventions_tenant_id`         | `tenant_id`        | `tenants(tenant_id)`     | (no rule stated)  |
| `fk_coaching_interventions_student_user_id`   | `student_user_id`  | `users(user_id)`         | (no rule stated)  |
| `fk_coaching_interventions_faculty_user_id`   | `faculty_user_id`  | `users(user_id)`         | (no rule stated)  |

> **Note**: No explicit cascade rule was specified for this table. The absence of
> a cascade rule implies the default `NO ACTION` / `RESTRICT` behaviour in
> PostgreSQL (the FK reference prevents deletion of the parent row while child
> rows exist). The team should confirm the intended behaviour at model-lock:
>
> - **Recommended**: `ON DELETE RESTRICT` for all three FKs — interventions are
>   compliance records and should not be automatically purged.

---

## Relationships

| Direction  | Related Table | Via Column          | Description                                          |
|------------|---------------|---------------------|------------------------------------------------------|
| Many → One | `tenants`     | `tenant_id`         | Intervention is scoped to one institution            |
| Many → One | `users`       | `student_user_id`   | The student who is the subject of the intervention   |
| Many → One | `users`       | `faculty_user_id`   | The faculty advisor who logged the intervention      |

> **Note**: There are **two separate FK relationships** from this table to `users`
> — one for the student, one for the faculty advisor. In SQLAlchemy, these must be
> configured with `foreign_keys=[...]` on each `relationship()` to disambiguate.

---

## Index Requirements

| Index Name                                              | Type   | Columns                                                        | Purpose                                                   |
|---------------------------------------------------------|--------|----------------------------------------------------------------|-----------------------------------------------------------|
| `ix_coaching_interventions_tenant_student_timestamp`    | B-Tree | `(tenant_id, student_user_id, recorded_timestamp)`            | Advising log rendering — per-student chronological view   |

---

## Expected Data Volume
- **Cardinality**: Moderate — one row per coaching event. Expect thousands to
  tens of thousands of rows per active tenant per academic year.
- **Write frequency**: Low-to-moderate (advisor-initiated; event-driven).
- **Read frequency**: Moderate — queried when loading a student's intervention
  history or generating compliance reports.
- **Immutability**: Rows should be treated as append-only audit entries; updates
  and deletes should be restricted at the application layer.

---

## Cross-Module Dependencies

| Module     | Table     | Relationship                                                       |
|------------|-----------|--------------------------------------------------------------------|
| `auth`     | `tenants` | `coaching_interventions.tenant_id → tenants.tenant_id`            |
| `auth`     | `users`   | `coaching_interventions.student_user_id → users.user_id`          |
| `auth`     | `users`   | `coaching_interventions.faculty_user_id → users.user_id`          |

---

## SQLAlchemy Notes
- `intervention_id` uses `postgresql.UUID(as_uuid=True)` with
  `server_default=text("gen_random_uuid()")`.
- `recorded_timestamp` uses `DateTime(timezone=True)` with
  `server_default=func.now()`.
- Two `relationship()` fields pointing to `User` must specify `foreign_keys`:
  ```python
  student = relationship("User", foreign_keys=[student_user_id])
  faculty  = relationship("User", foreign_keys=[faculty_user_id])
  ```
- `intervention_notes` is a `Text` column. Encryption/decryption is handled
  **entirely at the application layer** before writes and after reads — the
  database stores opaque ciphertext.

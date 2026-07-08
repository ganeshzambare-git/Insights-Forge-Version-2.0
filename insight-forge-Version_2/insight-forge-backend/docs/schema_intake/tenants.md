# Schema Intake — `tenants`

## Module
`auth`

## Purpose
Top-level multi-tenancy anchor. Every institution (university, school, etc.) is
registered as a single row in this table. All other tables reference `tenant_id`
to enforce row-level data isolation across institutions.

---

## Table Definition

### Table Name
`tenants`

### SQLAlchemy ORM Class Name
`Tenant`

---

## Columns

| Column       | PostgreSQL Type        | Nullable | Default                   | Constraints              | Description                              |
|--------------|------------------------|----------|---------------------------|--------------------------|------------------------------------------|
| `tenant_id`  | `UUID`                 | NOT NULL | `gen_random_uuid()`       | PRIMARY KEY              | Global unique institutional identifier   |
| `tenant_slug`| `VARCHAR(64)`          | NOT NULL | —                         | UNIQUE                   | URL-safe slug (e.g., `oxford-2025`)      |
| `tenant_name`| `VARCHAR(255)`         | NOT NULL | —                         |                          | Legal registered institution name        |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `CURRENT_TIMESTAMP`   |                          | UTC registration timestamp               |

---

## Primary Key
- `tenant_id` (UUID, server-generated via `gen_random_uuid()`)

## Unique Constraints
| Constraint Name              | Columns        |
|------------------------------|----------------|
| `uq_tenants_tenant_slug`     | `tenant_slug`  |

## Check Constraints
None.

## Foreign Keys
None. `tenants` is the root table; it has no upstream dependencies.

---

## Relationships

| Direction  | Related Table          | FK Column in Child   | Cascade Rule    |
|------------|------------------------|----------------------|-----------------|
| One → Many | `users`                | `users.tenant_id`    | ON DELETE RESTRICT |
| One → Many | `sessions`             | `sessions.tenant_id` | (no cascade stated) |
| One → Many | `cohorts`              | `cohorts.tenant_id`  | ON DELETE RESTRICT |
| One → Many | `student_metrics`      | `student_metrics.tenant_id` | ON DELETE RESTRICT |
| One → Many | `coaching_interventions` | `coaching_interventions.tenant_id` | (no cascade stated) |

---

## Index Requirements

No explicit indexes defined for this table. The `tenant_id` PK index is created
automatically by PostgreSQL. The `tenant_slug` UNIQUE constraint creates an
implicit B-Tree index.

---

## Expected Data Volume
- **Cardinality**: Very low — tens to low hundreds of rows (one per institution).
- **Write frequency**: Rare (institutional onboarding only).
- **Read frequency**: High — virtually every authenticated request joins or
  filters against `tenant_id`.

---

## Cross-Module Dependencies
This table is a **global dependency** consumed by every module:

| Module           | Table                    |
|------------------|--------------------------|
| `auth`           | `users`, `sessions`      |
| `academic`       | `cohorts`                |
| `analytics`      | `student_metrics`        |
| `interventions`  | `coaching_interventions` |

---

## SQLAlchemy Notes
- Use `postgresql.UUID(as_uuid=True)` with `server_default=text("gen_random_uuid()")`.
- `created_at` should use `server_default=func.now()` (server-side) and
  `timezone=True` on the `DateTime` column type.
- Map `tenant_slug` with `unique=True` in the column definition.

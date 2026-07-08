# Schema Intake — `cohorts`

## Module
`academic`

## Purpose
Represents a named grouping of students within a department (e.g., a year-group
or class section). Cohorts act as the structural unit that links students to a
course/programme for the purposes of grade analytics and advisor assignment.

---

## Table Definition

### Table Name
`cohorts`

### SQLAlchemy ORM Class Name
`Cohort`

---

## Columns

| Column             | PostgreSQL Type | Nullable | Default             | Constraints               | Description                                 |
|--------------------|-----------------|----------|---------------------|---------------------------|---------------------------------------------|
| `cohort_id`        | `UUID`          | NOT NULL | `gen_random_uuid()` | PRIMARY KEY               | Unique student class group identifier       |
| `tenant_id`        | `UUID`          | NOT NULL | —                   | FK → `tenants(tenant_id)` | Institutional boundary anchor               |
| `cohort_code`      | `VARCHAR(32)`   | NOT NULL | —                   |                           | Short cohort label (e.g., `'CompSci-A'`)    |
| `department_scope` | `VARCHAR(128)`  | NOT NULL | —                   |                           | Owning department (e.g., `'Science'`)       |

---

## Primary Key
- `cohort_id` (UUID, server-generated via `gen_random_uuid()`)

## Unique Constraints
None explicitly stated.

> **Design note**: Consider adding a composite unique constraint
> `(tenant_id, cohort_code)` at model-lock to prevent duplicate cohort codes
> within the same institution.

## Check Constraints
None.

## Foreign Keys
| Constraint Name          | Column      | References               | On Delete |
|--------------------------|-------------|--------------------------|-----------|
| `fk_cohorts_tenant_id`   | `tenant_id` | `tenants(tenant_id)`     | RESTRICT  |

---

## Relationships

| Direction  | Related Table     | Description                                           |
|------------|-------------------|-------------------------------------------------------|
| Many → One | `tenants`         | Cohort belongs to one tenant                          |
| One → Many | `student_metrics` | Cohort groups many student performance records        |

---

## Index Requirements

No explicit indexes were specified for this table. The `cohort_id` PK index is
created automatically. The `tenant_id` FK column participates in the compound
index on `student_metrics` downstream.

> **Recommendation**: If cohort lookup by `(tenant_id, cohort_code)` is frequent
> (e.g., dashboard filtering), add a B-Tree index on `(tenant_id, cohort_code)`
> at model-lock.

---

## Expected Data Volume
- **Cardinality**: Low to moderate — typically tens to low hundreds of cohorts
  per tenant (one per programme-year or class section).
- **Write frequency**: Low (academic year boundaries).
- **Read frequency**: Moderate — used in join queries when building advisor
  dashboards and analytics views.

---

## Cross-Module Dependencies

| Module      | Table             | Relationship                                        |
|-------------|-------------------|-----------------------------------------------------|
| `analytics` | `student_metrics` | `student_metrics.cohort_id → cohorts.cohort_id`    |

---

## SQLAlchemy Notes
- Use `postgresql.UUID(as_uuid=True)` with `server_default=text("gen_random_uuid()")`.
- `tenant_id` FK with `ondelete="RESTRICT"` in the `ForeignKey` definition.
- The `student_metrics` relationship is defined as a `back_populates` on the
  `StudentMetric` model side (many → one pointing back to `Cohort`).

# Schema Intake — `student_metrics`

## Module
`analytics`

## Purpose
Stores per-student academic performance snapshots. Each row captures a student's
raw average grade, ML-curved normalized score, attendance percentage, and a
traffic-light risk status (`'Safe'`, `'Amber'`, `'Critical'`). This table is the
primary data source for advisor dashboards, early-warning systems, and reporting
exports.

---

## Table Definition

### Table Name
`student_metrics`

### SQLAlchemy ORM Class Name
`StudentMetric`

---

## Columns

| Column                     | PostgreSQL Type | Nullable | Default                          | Constraints                        | Description                                            |
|----------------------------|-----------------|----------|----------------------------------|------------------------------------|--------------------------------------------------------|
| `metric_id`                | `BIGINT`        | NOT NULL | `GENERATED ALWAYS AS IDENTITY`   | PRIMARY KEY                        | Auto-incrementing surrogate key                        |
| `tenant_id`                | `UUID`          | NOT NULL | —                                | FK → `tenants(tenant_id)`         | Tenant data segregation                                |
| `student_user_id`          | `UUID`          | NOT NULL | —                                | FK → `users(user_id)`             | Student identifier link                                |
| `cohort_id`                | `UUID`          | NOT NULL | —                                | FK → `cohorts(cohort_id)`         | Course structure grouping                              |
| `raw_average_grade`        | `NUMERIC(5,2)`  | NOT NULL | —                                | CHECK ≤ 100.00                     | Raw academic standing score                            |
| `normalized_grade_score`   | `NUMERIC(5,2)`  | NULL     | —                                |                                    | Scikit-learn bell-curve adjusted score (nullable)      |
| `attendance_percentage`    | `NUMERIC(5,2)`  | NOT NULL | —                                | CHECK ≤ 100.00                     | Cumulative attendance as a percentage                  |
| `success_indicator_status` | `VARCHAR(24)`   | NOT NULL | —                                | CHECK (see below)                  | Risk label: `'Safe'`, `'Amber'`, `'Critical'`          |

---

## Primary Key
- `metric_id` (BIGINT, `GENERATED ALWAYS AS IDENTITY` — PostgreSQL identity column,
  not a sequence default. SQLAlchemy maps this via `Identity(always=True)`.)

## Unique Constraints
None.

## Check Constraints
| Constraint Name                               | Expression                                                                 |
|-----------------------------------------------|----------------------------------------------------------------------------|
| `ck_student_metrics_raw_grade`                | `raw_average_grade >= 0 AND raw_average_grade <= 100.00`                   |
| `ck_student_metrics_attendance`               | `attendance_percentage >= 0 AND attendance_percentage <= 100.00`           |
| `ck_student_metrics_success_indicator_status` | `success_indicator_status IN ('Safe', 'Amber', 'Critical')`                |

## Foreign Keys
| Constraint Name                      | Column             | References               | On Delete |
|--------------------------------------|--------------------|--------------------------|-----------|
| `fk_student_metrics_tenant_id`       | `tenant_id`        | `tenants(tenant_id)`     | RESTRICT  |
| `fk_student_metrics_student_user_id` | `student_user_id`  | `users(user_id)`         | CASCADE   |
| `fk_student_metrics_cohort_id`       | `cohort_id`        | `cohorts(cohort_id)`     | RESTRICT  |

> **Cascade notes**:
> - `student_user_id → users`: `ON DELETE CASCADE` — if a user account is
>   deleted, their metric history is purged.
> - `tenant_id → tenants`: `ON DELETE RESTRICT` — tenant cannot be deleted while
>   student metric data exists.
> - `cohort_id → cohorts`: `ON DELETE RESTRICT` — cohort cannot be deleted if
>   historical grade data is linked.

---

## Relationships

| Direction  | Related Table | Description                                       |
|------------|---------------|---------------------------------------------------|
| Many → One | `tenants`     | Metrics belong to one tenant                      |
| Many → One | `users`       | Metrics belong to one student user                |
| Many → One | `cohorts`     | Metrics are grouped by cohort                     |

---

## Index Requirements

| Index Name                                           | Type   | Columns                                                     | Purpose                                                   |
|------------------------------------------------------|--------|-------------------------------------------------------------|-----------------------------------------------------------|
| `ix_student_metrics_tenant_cohort_status`            | B-Tree | `(tenant_id, cohort_id, success_indicator_status)`          | Advisor grid view — filter by cohort and risk status      |
| `ix_student_metrics_tenant_normalized_grade`         | B-Tree | `(tenant_id, normalized_grade_score DESC NULLS LAST)`       | Performance curve reads — ordered grade reports per tenant |

---

## Expected Data Volume
- **Cardinality**: High — one or more rows per student per reporting period.
  Expect millions of rows per large tenant over time.
- **Write frequency**: Moderate-to-high (updated when grades or attendance data
  is ingested or recalculated by the ML pipeline).
- **Read frequency**: Very high — the primary source for all dashboard widgets
  and report exports.
- **Partitioning consideration**: If volume grows beyond tens of millions of rows,
  range-partition by `tenant_id` or `cohort_id` should be evaluated.

---

## Cross-Module Dependencies

| Module          | Table                    | Relationship                                                   |
|-----------------|--------------------------|----------------------------------------------------------------|
| `auth`          | `tenants`                | `student_metrics.tenant_id → tenants.tenant_id`               |
| `auth`          | `users`                  | `student_metrics.student_user_id → users.user_id`             |
| `academic`      | `cohorts`                | `student_metrics.cohort_id → cohorts.cohort_id`               |
| `interventions` | `coaching_interventions` | Interventions reference same `student_user_id` (no direct FK) |

---

## SQLAlchemy Notes
- `metric_id` uses `BigInteger` with `Identity(always=True)` (requires
  SQLAlchemy 1.4+ and `postgresql.IDENTITY`).
- `raw_average_grade` and `attendance_percentage` use `Numeric(precision=5, scale=2)`.
- `normalized_grade_score` is `nullable=True`.
- `success_indicator_status` uses a `CheckConstraint` or a PostgreSQL `ENUM` type
  (decision deferred to model-lock stage).
- All FK columns use `ondelete="RESTRICT"` except `student_user_id` which uses
  `ondelete="CASCADE"`.

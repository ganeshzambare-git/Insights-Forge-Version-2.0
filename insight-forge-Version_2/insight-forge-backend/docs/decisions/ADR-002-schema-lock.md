# ADR-002 --- Insight Forge v2.0 Production Schema Lock

## Status

Locked

## Purpose

This document records the final database architecture decisions required
before the approved Insight Forge v2.0 module schemas are converted into
SQLAlchemy ORM models, Alembic migrations, PostgreSQL constraints,
indexes, and Row-Level Security policies.

## Authoritative Schema Sources

-   `docs/schema_intake/tenants.md`
-   `docs/schema_intake/users.md`
-   `docs/schema_intake/sessions.md`
-   `docs/schema_intake/cohorts.md`
-   `docs/schema_intake/student_metrics.md`
-   `docs/schema_intake/coaching_interventions.md`

## Authority Rule

The received module schemas define the intended domain structure. This
ADR resolves production-level ambiguities and is authoritative when a
schema proposal omits or conflicts with a database engineering detail.

No production schema change may bypass schema review, ADR updates when
architecture changes, SQLAlchemy model updates, Alembic migrations,
migration verification, and PostgreSQL validation.

------------------------------------------------------------------------

# Decision 1 --- Timestamp Strategy

## Status

Locked \## Decision Production models will follow timestamp columns
explicitly defined by the authoritative schema. A global timestamp mixin
will not automatically be inherited by every model. \## Rules - Do not
add `created_at` unless the locked schema defines it. - Do not add
`updated_at` unless the locked schema defines it. - Do not silently add
audit columns during ORM implementation. - Timestamp columns must be
timezone-aware where specified. - Future timestamp additions require a
reviewed migration. \## Foundation Impact
`app/models/mixins/timestamp.py` remains reusable infrastructure but may
only be used when its complete column set exactly matches the target
table.

------------------------------------------------------------------------

# Decision 2 --- Foreign-Key Delete Rules

## Status

Locked \## Locked Rules

  Child Table                Foreign Key         Parent Table   Delete Rule
  -------------------------- ------------------- -------------- -------------
  `users`                    `tenant_id`         `tenants`      `RESTRICT`
  `sessions`                 `user_id`           `users`        `CASCADE`
  `sessions`                 `tenant_id`         `tenants`      `RESTRICT`
  `cohorts`                  `tenant_id`         `tenants`      `RESTRICT`
  `student_metrics`          `tenant_id`         `tenants`      `RESTRICT`
  `student_metrics`          `student_user_id`   `users`        `CASCADE`
  `student_metrics`          `cohort_id`         `cohorts`      `RESTRICT`
  `coaching_interventions`   `tenant_id`         `tenants`      `RESTRICT`
  `coaching_interventions`   `student_user_id`   `users`        `RESTRICT`
  `coaching_interventions`   `faculty_user_id`   `users`        `RESTRICT`

## Rules

-   Every foreign key must explicitly define `ondelete`.
-   ORM cascade settings must not contradict database behavior.
-   `CASCADE` is limited to lifecycle-dependent records.
-   Institutional, historical, and intervention records default to
    protection.

------------------------------------------------------------------------

# Decision 3 --- User Role Storage

## Status

Locked \## Decision User roles will use `VARCHAR(32)` with a PostgreSQL
`CHECK` constraint. PostgreSQL native ENUM will not be used. \## Allowed
Values - `Admin` - `Dean` - `Faculty` - `Student` \## Constraint

``` sql
CHECK (assigned_role IN ('Admin', 'Dean', 'Faculty', 'Student'))
```

## Rules

-   Values are case-sensitive.
-   PostgreSQL is the final validation authority.
-   SQLAlchemy and Pydantic must use the same role set.
-   New roles require a reviewed schema change and migration.

------------------------------------------------------------------------

# Decision 4 --- Corporate Email Uniqueness

## Status

Locked \## Decision `corporate_email` will be globally unique across the
platform. \## Constraint

``` sql
UNIQUE (corporate_email)
```

## Rules

-   The same corporate email cannot create multiple user identities
    across tenants.
-   Email values must be normalized before persistence.
-   Application logic must lowercase and trim email values before
    validation. \## Future Change If cross-institution membership
    becomes a product requirement, revisit this decision before changing
    uniqueness to `UNIQUE (tenant_id, corporate_email)`.

------------------------------------------------------------------------

# Decision 5 --- PostgreSQL-Native Session IP Type

## Status

Locked \## Decision `sessions.ingress_ip` will use PostgreSQL native
`INET`. \## ORM Rule Use
`from sqlalchemy.dialects.postgresql import INET`. Do not store IP
addresses as integers or generic strings.

------------------------------------------------------------------------

# Decision 6 --- JWT JTI Index Strategy

## Status

Locked \## Decision `jwt_jti` will remain `UNIQUE`. No additional HASH
index will be created initially. \## Rationale A unique constraint
already creates an index suitable for exact equality lookups. A second
index would add storage and write overhead without demonstrated
evidence. \## Future Rule Add another index only after benchmark or
query-plan evidence demonstrates a real requirement.

------------------------------------------------------------------------

# Decision 7 --- Student Metrics Reporting Period

## Status

Locked with Required Schema Enhancement \## Decision `student_metrics`
must include an explicit reporting-period identifier before production
implementation. \## Required Column

``` text
reporting_period VARCHAR(32) NOT NULL
```

Examples: `2026-SEM-1`, `2026-SEM-2`, `2026-Q1`. \## Rationale The
received schema permits multiple metric records for a student but lacks
a reliable temporal dimension. \## Rule The reporting-period format must
be validated consistently by ingestion and application layers.

------------------------------------------------------------------------

# Decision 8 --- Cross-Tenant Referential Integrity

## Status

Locked \## Decision RLS alone is not sufficient protection against
mismatched tenant relationships. Every tenant-owned relationship must be
validated so a child row cannot point to a parent belonging to another
tenant. \## Enforcement Strategy 1. PostgreSQL Row-Level Security 2.
Transaction-local tenant context 3. Service-layer tenant validation 4.
Integration tests for cross-tenant rejection \## Rule No repository or
service may trust a client-supplied `tenant_id` without validated
authentication context.

------------------------------------------------------------------------

# Decision 9 --- Encryption Strategy

## Status

Locked at Architecture Level \## Protected Fields -
`users.totp_secret` - `coaching_interventions.intervention_notes` \##
Decision Sensitive application fields will be encrypted before
persistence. Plaintext sensitive values must never be stored in
PostgreSQL. \## Rules - Encryption and decryption occur through
centralized infrastructure. - Business services must not implement
custom encryption independently. - Encryption keys must never be stored
in source code, Git, or database rows. - Key material must come from
secure environment or secret-management systems. - Models requiring
encrypted fields must not be completed until the encryption contract is
implemented and tested. \## Implementation Location
`app/db/types/encrypted.py`

------------------------------------------------------------------------

# Decision 10 --- Multi-Tenant Row-Level Security

## Status

Locked \## Decision Every tenant-owned application table must have
PostgreSQL Row-Level Security enabled. \## Tenant Context

``` sql
SET LOCAL app.current_tenant_id = '<validated-tenant-uuid>';
```

## Rules

-   Tenant context must be established inside the transaction.
-   Tenant identity must come from validated authentication context.
-   Client-supplied tenant identifiers are never trusted directly.
-   Missing tenant context must fail closed.
-   Cross-tenant reads and writes must be rejected.
-   RLS behavior requires dedicated security integration tests. \##
    Initial Tenant-Owned Tables `users`, `sessions`, `cohorts`,
    `student_metrics`, `coaching_interventions`.

------------------------------------------------------------------------

# Decision 11 --- Primary-Key Strategy

## Status

Locked \## Decision Use the primary-key types defined by the received
schemas. \## UUID Tables `tenants.tenant_id`, `users.user_id`,
`sessions.session_id`, `cohorts.cohort_id`,
`coaching_interventions.intervention_id`. \## High-Volume Metric Table
`student_metrics.metric_id` uses:

``` sql
BIGINT GENERATED ALWAYS AS IDENTITY
```

## Rule

Application code must not manually generate identity-managed metric
primary keys.

------------------------------------------------------------------------

# Decision 12 --- UUID Generation

## Status

Locked \## Decision PostgreSQL will generate schema-defined UUID primary
keys using:

``` sql
gen_random_uuid()
```

## Requirement

Function availability must be verified by the initial migration before
table creation.

------------------------------------------------------------------------

# Decision 13 --- Constraint Naming

## Status

Locked \## Decision All constraints use the SQLAlchemy metadata naming
convention in `app/db/base.py`. \## Required Prefixes - `pk_` ---
primary keys - `fk_` --- foreign keys - `uq_` --- unique constraints -
`ck_` --- check constraints - `ix_` --- indexes \## Rule Unnamed
production constraints are not allowed.

------------------------------------------------------------------------

# Decision 14 --- Index Strategy

## Status

Locked \## Decision Indexes follow approved schema recommendations but
must be reviewed for duplication before migration generation. \##
Initial Index Targets \### Users `BTREE (tenant_id, assigned_role)` \###
Student Metrics `BTREE (tenant_id, cohort_id, success_indicator_status)`
`BTREE (tenant_id, normalized_grade_score DESC)` \### Coaching
Interventions `BTREE (tenant_id, student_user_id, recorded_timestamp)`
\## Rules - Do not duplicate indexes already provided by primary-key or
unique constraints. - Every index must have a documented query
purpose. - Additional indexes require query-plan or benchmark
justification. - Index definitions must be reviewed before production
migration.

------------------------------------------------------------------------

# Decision 15 --- Schema Ownership and Change Control

## Status

Locked \## Decision Module owners propose schema requirements. The
Backend and Database Architecture layer owns integration review, naming
consistency, referential integrity, migration generation, RLS
implementation, performance review, and production application. \##
Protected Paths `app/models/`, `app/db/`, `migrations/`, and
`database/rls/` require database architecture review before
modification.

------------------------------------------------------------------------

# Decision 16 --- Migration Authority

## Status

Locked \## Decision Alembic is the only approved mechanism for
production schema evolution. \## Forbidden Production Practices -
`Base.metadata.create_all()` - manual table creation through database
consoles - untracked production DDL - editing already-applied migration
files - deleting migration history to resolve conflicts \## Required
Flow Locked Schema → SQLAlchemy Models → Alembic Revision → Migration
Review → Upgrade Test → Downgrade Test → RLS Test → Production
Application.

------------------------------------------------------------------------

# Decision 17 --- Neon Connection Usage

## Status

Locked \## Decision Application runtime uses the pooled Neon PostgreSQL
connection. Migration connectivity will be evaluated separately before
Alembic execution. \## Rules - Credentials exist only in `.env` or
production secret storage. - `.env.example` contains no secrets. -
Connection strings must never appear in Git, screenshots, logs, or
documents. - Exposed credentials must be rotated immediately. -
Connection verification must never print the connection string.

------------------------------------------------------------------------

# Decision 18 --- Model Implementation Order

## Status

Locked \## Required Dependency Order 1. Tenant 2. User 3. Session 4.
Cohort 5. StudentMetric 6. CoachingIntervention

No model may be implemented before all parent dependencies required by
its foreign keys are defined.

------------------------------------------------------------------------

# Decision 19 --- Production Migration Boundary

## Status

Locked \## Decision No migration will be applied to Neon until all six
models: - load successfully - pass metadata tests - pass relationship
tests - pass constraint tests - pass schema review

The first migration will represent one reviewed production baseline.

------------------------------------------------------------------------

# Final Schema Lock Status

## Status

LOCKED FOR ORM IMPLEMENTATION

The six received module schemas are accepted as the domain foundation
subject to the production decisions and required enhancement recorded in
this ADR.

## Next Phase

SQLAlchemy Model Construction → Metadata Validation → Alembic
Infrastructure → Baseline Migration Review → Neon Application → RLS
Enforcement.

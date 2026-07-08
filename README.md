# Insight Forge V2.0 — Backend & Database Foundation

## Project Status

**Database Foundation: COMPLETE ✅**

**Test Status: 39/39 PASSING ✅**

This repository contains the completed production-grade database foundation for Insight Forge V2.0.

The database architecture, ORM models, Alembic migrations, multi-tenant security, Row-Level Security (RLS), runtime database role separation, schema synchronization, and live tenant-isolation testing have been completed and verified.

---

# Work Completed

## 1. Production Database Schema

The following 6 production tables have been implemented and deployed:

1. `tenants`
2. `users`
3. `cohorts`
4. `sessions`
5. `student_metrics`
6. `coaching_interventions`

The schema is deployed on PostgreSQL using Neon.

---

## 2. Multi-Tenant Architecture

Insight Forge V2.0 uses a tenant-isolated architecture.

The following tables are tenant-owned:

- `users`
- `cohorts`
- `sessions`
- `student_metrics`
- `coaching_interventions`

Every tenant-owned record is connected to a `tenant_id`.

Tenant isolation is enforced at the PostgreSQL database level and is not dependent only on application code.

---

## 3. Row-Level Security (RLS)

PostgreSQL Row-Level Security has been enabled and forced on all tenant-owned tables.

Implemented security behavior:

- Tenant A can access only Tenant A data.
- Tenant B can access only Tenant B data.
- Tenant A cannot read Tenant B data.
- Tenant B cannot read Tenant A data.
- Cross-tenant writes are blocked.
- Missing tenant context exposes no tenant-owned test data.
- RLS is enforced using transaction-local PostgreSQL tenant context.

The PostgreSQL session variable used by the policies is:

```text
app.current_tenant_id

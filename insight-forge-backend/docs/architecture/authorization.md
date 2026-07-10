# Authorization & Access Control — Insight Forge V2

This document details the multi-tenant authorization matrix and database security constraints.

---

## 1. Role-Based Access Control (RBAC)

The platform supports 4 user roles with hierarchical capability scopes:

| Role | Description | Access Scope |
| :--- | :--- | :--- |
| **Admin** | System operator. | Full access to tenant configuration, users, and audit logs. |
| **Dean** | Academic department director. | Access to tenant metrics, cohorts, faculty, and reporting views. |
| **Faculty** | Instructor / Tutor. | Access to student metrics and coaching interventions for assigned cohorts. |
| **Student** | Learner. | Read-only access to their own academic grades and attendance progress. |

---

## 2. Row-Level Security (RLS)

Every database table (except the core global `tenants` table) is isolated by PostgreSQL **Row-Level Security** policies.

- **Isolation Rule**: Queries are restricted to the tenant matching the active transaction session variables.
- **Session Context**: The application session establishes the active tenant identifier using SQL variables before query execution:
  ```sql
  SET LOCAL app.current_tenant_id = 'tenant-uuid';
  ```
- **RLS Bypass Prevention**: API connections bind to limited-privilege database roles (`tenant_app_user`) to guarantee RLS rules are forced at the engine level.

---

## 3. Safe Multi-Tenant Repository Injections

To prevent accidental cross-tenant leaks:
1. Every query executed in repositories must include `tenant_id` filters.
2. The `tenant_id` is parsed from the validated JWT token during API request injection and passed directly down to the Service Layer.

---

## 4. API Dependency Guards

FastAPI endpoints enforce RBAC using the type-safe `Role` enum and declarative dependency guards:
- **Enum definition**: `app.core.roles.Role` (`Admin`, `Dean`, `Faculty`, `Student`)
- **Guard class**: `app.dependencies.auth.RequireRoles`
- **Example Usage**:
  ```python
  @router.post("/metrics", dependencies=[Depends(RequireRoles(Role.ADMIN, Role.DEAN))])
  async def log_metric(...):
      ...
  ```
  If a user has an invalid role, it raises `AuthorizationError` which translates automatically at the API layer to `403 Forbidden`.


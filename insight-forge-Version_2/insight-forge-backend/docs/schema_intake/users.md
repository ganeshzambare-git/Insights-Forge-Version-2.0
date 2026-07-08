# Schema Intake — `users`

## Module
`auth`

## Purpose
Stores all authenticated principals across the platform — Admins, Deans, Faculty,
and Students — scoped to a single tenant. Role-based access control is encoded
directly in `assigned_role`. MFA state and encrypted TOTP seeds are also housed
here.

---

## Table Definition

### Table Name
`users`

### SQLAlchemy ORM Class Name
`User`

---

## Columns

| Column            | PostgreSQL Type        | Nullable | Default               | Constraints                             | Description                                      |
|-------------------|------------------------|----------|-----------------------|-----------------------------------------|--------------------------------------------------|
| `user_id`         | `UUID`                 | NOT NULL | `gen_random_uuid()`   | PRIMARY KEY                             | Unique user identifier                           |
| `tenant_id`       | `UUID`                 | NOT NULL | —                     | FK → `tenants(tenant_id)`              | Tenant isolation linkage                         |
| `corporate_email` | `VARCHAR(255)`         | NOT NULL | —                     | UNIQUE                                  | Institutional email address                      |
| `password_hash`   | `VARCHAR(255)`         | NOT NULL | —                     |                                         | Argon2id password hash                           |
| `assigned_role`   | `VARCHAR(32)`          | NOT NULL | —                     | CHECK (see below)                       | Role label: `'Admin'`, `'Dean'`, `'Faculty'`, `'Student'` |
| `is_mfa_enabled`  | `BOOLEAN`              | NOT NULL | `TRUE`                |                                         | MFA enforcement flag                             |
| `totp_secret`     | `VARCHAR(128)`         | NULL     | —                     |                                         | AES-256 encrypted TOTP seed (nullable)           |

---

## Primary Key
- `user_id` (UUID, server-generated via `gen_random_uuid()`)

## Unique Constraints
| Constraint Name                | Columns            |
|--------------------------------|--------------------|
| `uq_users_corporate_email`     | `corporate_email`  |

## Check Constraints
| Constraint Name              | Expression                                                                          |
|------------------------------|-------------------------------------------------------------------------------------|
| `ck_users_assigned_role`     | `assigned_role IN ('Admin', 'Dean', 'Faculty', 'Student')`                          |

## Foreign Keys
| Constraint Name          | Column      | References               | On Delete       |
|--------------------------|-------------|--------------------------|-----------------|
| `fk_users_tenant_id`     | `tenant_id` | `tenants(tenant_id)`     | RESTRICT        |

---

## Relationships

| Direction  | Related Table            | Description                                    |
|------------|--------------------------|------------------------------------------------|
| Many → One | `tenants`                | User belongs to one tenant                     |
| One → Many | `sessions`               | User can have multiple active sessions         |
| One → Many | `student_metrics`        | User (as student) has performance records      |
| One → Many | `coaching_interventions` | User appears as student **or** faculty advisor |

---

## Index Requirements

| Index Name                     | Type   | Columns                         | Purpose                                  |
|--------------------------------|--------|---------------------------------|------------------------------------------|
| `ix_users_tenant_id_role`      | B-Tree | `(tenant_id, assigned_role)`   | Fast role-filtered queries per tenant    |

---

## Expected Data Volume
- **Cardinality**: Tens of thousands per tenant; potentially millions across all tenants.
- **Write frequency**: Moderate (user registrations, role changes).
- **Read frequency**: Very high — authenticated on every request.

---

## Cross-Module Dependencies

| Module           | Table                    | Relationship                                     |
|------------------|--------------------------|--------------------------------------------------|
| `auth`           | `sessions`               | `sessions.user_id → users.user_id`              |
| `analytics`      | `student_metrics`        | `student_metrics.student_user_id → users.user_id` |
| `interventions`  | `coaching_interventions` | Both `student_user_id` and `faculty_user_id` FK |

---

## SQLAlchemy Notes
- Use `postgresql.UUID(as_uuid=True)` with `server_default=text("gen_random_uuid()")`.
- `assigned_role` should use a SQLAlchemy `CheckConstraint` or a PostgreSQL-native
  `ENUM` type (document which is chosen at model-lock stage).
- `is_mfa_enabled` maps to `Boolean(server_default=true())`.
- `totp_secret` is nullable; application layer is responsible for AES-256
  encryption/decryption before writing/reading this field.
- `corporate_email` uniqueness is **global** (not per-tenant) — one email can only
  exist in one tenant across the entire platform.

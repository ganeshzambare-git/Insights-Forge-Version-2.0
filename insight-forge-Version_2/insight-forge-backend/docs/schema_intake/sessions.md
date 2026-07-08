# Schema Intake — `sessions`

## Module
`auth`

## Purpose
Tracks active authenticated sessions for JWT replay-attack prevention and
IP-level audit trails. Each row represents one issued JWT; once `expires_at`
passes the session is logically dead. The `jwt_jti` (JWT ID) uniqueness
constraint allows the server to detect and block token replay.

---

## Table Definition

### Table Name
`sessions`

### SQLAlchemy ORM Class Name
`Session`

---

## Columns

| Column       | PostgreSQL Type            | Nullable | Default             | Constraints                         | Description                              |
|--------------|----------------------------|----------|---------------------|-------------------------------------|------------------------------------------|
| `session_id` | `UUID`                     | NOT NULL | `gen_random_uuid()` | PRIMARY KEY                         | Unique session token                     |
| `user_id`    | `UUID`                     | NOT NULL | —                   | FK → `users(user_id)`              | Authenticated entity link                |
| `tenant_id`  | `UUID`                     | NOT NULL | —                   | FK → `tenants(tenant_id)`          | Session tenant boundary                  |
| `jwt_jti`    | `VARCHAR(255)`             | NOT NULL | —                   | UNIQUE                              | JWT ID — used to detect replayed tokens  |
| `expires_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | —                   |                                     | Absolute session expiry (15-min window)  |
| `ingress_ip` | `INET`                     | NOT NULL | —                   |                                     | Client IP captured at login              |

---

## Primary Key
- `session_id` (UUID, server-generated via `gen_random_uuid()`)

## Unique Constraints
| Constraint Name           | Columns     |
|---------------------------|-------------|
| `uq_sessions_jwt_jti`     | `jwt_jti`   |

## Check Constraints
None.

## Foreign Keys
| Constraint Name              | Column      | References               | On Delete         |
|------------------------------|-------------|--------------------------|-------------------|
| `fk_sessions_user_id`        | `user_id`   | `users(user_id)`         | (no rule stated)  |
| `fk_sessions_tenant_id`      | `tenant_id` | `tenants(tenant_id)`     | (no rule stated)  |

> **Note**: No explicit cascade rule was specified for sessions in the requirements
> document. At model-lock, the team should decide between `ON DELETE CASCADE`
> (purge sessions when user is deleted) or `ON DELETE SET NULL` (retain audit log).
> Current recommendation: `ON DELETE CASCADE` for `user_id` to avoid orphan rows.

---

## Relationships

| Direction  | Related Table | Description                                      |
|------------|---------------|--------------------------------------------------|
| Many → One | `users`       | Session belongs to one authenticated user        |
| Many → One | `tenants`     | Session is bound to one institutional tenant     |

---

## Index Requirements

| Index Name                | Type | Columns      | Purpose                                           |
|---------------------------|------|--------------|---------------------------------------------------|
| `ix_sessions_jwt_jti`     | Hash | `(jwt_jti)`  | O(1) JWT lookup for replay-attack validation      |

> **Note**: PostgreSQL Hash indexes are not WAL-logged prior to PG10. Neon runs
> PG15+, so Hash indexes are safe to use here.

---

## Expected Data Volume
- **Cardinality**: High and volatile — one row per active JWT (15-min TTL).
  Expect millions of rows under load; a background job or partitioning by
  `expires_at` should be planned for pruning expired sessions.
- **Write frequency**: Very high (one insert per login).
- **Read frequency**: Very high (one lookup per authenticated API call).
- **Delete/Expiry**: Rows should be swept periodically (e.g., a cron job or
  `pg_cron`) where `expires_at < NOW()`.

---

## Cross-Module Dependencies

| Module | Table   | Relationship                          |
|--------|---------|---------------------------------------|
| `auth` | `users` | `sessions.user_id → users.user_id`   |
| `auth` | `tenants` | `sessions.tenant_id → tenants.tenant_id` |

Sessions are self-contained within the `auth` module and have **no downstream
dependencies** in other modules.

---

## SQLAlchemy Notes
- Use `postgresql.UUID(as_uuid=True)` for `session_id`, `user_id`, `tenant_id`.
- Use `postgresql.INET` for `ingress_ip` (maps to Python `str`; SQLAlchemy does
  not have a built-in INET type — use `sa.String` with a custom TypeDecorator or
  the `sqlalchemy-utils` `IPAddressType`).
- `expires_at` maps to `DateTime(timezone=True)` with no server default (set
  explicitly by the application layer at session creation time).
- `jwt_jti` uniqueness is enforced both at the DB level (UNIQUE constraint) and
  should be validated at the application layer before insert.

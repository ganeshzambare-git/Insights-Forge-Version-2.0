# Database Architecture — Insight Forge V2

This document describes the database connection management, driver selection, and pooling rules.

---

## 1. Persistency Engine

- **Database**: Neon Serverless PostgreSQL.
- **Asynchronous Driver**: `psycopg` (v3 async connection driver).
- **ORM**: SQLAlchemy 2.0 (leveraging async extension wrappers).

---

## 2. Connection String Schemes

Neon utilizes traditional `postgresql://` connection strings. For SQLAlchemy async mode compatibility, the application settings automatically rewrite the connection string scheme to `postgresql+psycopg://` at runtime:

```python
@property
def async_database_url(self) -> str:
    if self.DATABASE_URL.startswith("postgresql://"):
        return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    return self.DATABASE_URL
```

---

## 3. Connection Pool Settings

The connection pool settings are configurable via environment variables to scale smoothly under varying loads:

| Config | Default | Description |
| :--- | :--- | :--- |
| `DB_POOL_SIZE` | `20` | The number of permanent connections kept in the pool. |
| `DB_MAX_OVERFLOW` | `10` | The number of temporary connections allowed beyond `pool_size`. |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait for an available connection from the pool before raising an error. |
| `DB_POOL_RECYCLE` | `1800` | Connection age in seconds after which it is recycled (clears memory leaks). |

---

## 4. Alembic Migrations

- **Directory**: `/migrations`
- **Metadata Configuration**: Uses the `NAMING_CONVENTION` mapping in `Base.metadata` to ensure clean, deterministic constraint names across dev and production.

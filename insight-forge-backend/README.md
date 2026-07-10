# Insight Forge v2.0 Backend

Enterprise-grade multi-tenant educational intelligence platform backend built using FastAPI, SQLAlchemy, and psycopg3.

---

## Backend Status

- [x] Database Layer
- [x] Application Foundation
- [ ] Repository Layer (Next)
- [ ] Service Layer
- [ ] Authentication
- [ ] Middleware
- [ ] API Endpoints
- [ ] Ingestion Pipelines
- [ ] Analytics Engine

---

## Getting Started

### Prerequisites

- Python 3.13.5
- PostgreSQL (Neon Database connection string)

### Environment Variables

Configure these variables inside your `.env` file at the backend directory root:

```ini
# Application Configurations
APP_NAME="Insight Forge"
APP_VERSION="2.0.0"
APP_ENV="development"
DEBUG=true

# Database Configurations
DATABASE_URL="postgresql://<user>:<password>@<host>/<db>?sslmode=require"
MIGRATION_DATABASE_URL="postgresql://<user>:<password>@<host>/<db>?sslmode=require"

# Async Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Security
SECRET_KEY="your-secret-key-goes-here"
JWT_ALGORITHM="RS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Observability
LOG_LEVEL="INFO"
```

---

## Running the Application

### Development (Windows Event Loop Compatible)

On Windows platforms, `psycopg3` requires `SelectorEventLoop` to function asynchronously. Using the standard CLI `uvicorn` runner directly can trigger `InterfaceError`. 

To run safely in development mode, execute:

```bash
python serve.py
```

This script sets the `SelectorEventLoopPolicy` globally before Uvicorn starts the server process.

### Production

On production platforms (typically Linux environments where `SelectorEventLoop` or `uvloop` is standard), start the server directly using:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

# Insight Forge Version 2.0

Insight Forge is a full-stack educational decision intelligence platform with a FastAPI backend and a Next.js frontend.

## Repository Layout

- `insight-forge-backend/` - FastAPI application, SQLAlchemy models, migrations, services, tests, and operational scripts.
- `insight-forge-frontend/` - Next.js React frontend organized by enterprise feature domains.
- `database/`, `docs/`, and `workflows/` content live under the backend and root workflow folders.
- `brain/` contains project architecture, roadmap, patterns, and implementation memory.

## Local Development

Backend:

```powershell
cd insight-forge-backend
python serve.py
```

Frontend build:

```powershell
cd insight-forge-frontend
npm install
npm run build
```

The backend can serve the static frontend export from `insight-forge-frontend/out` through the same Uvicorn host.

## Environment

Copy `.env.example` values into local `.env` files and provide real secrets locally. Do not commit `.env`, build output, virtual environments, logs, or dependency folders.

## License

MIT

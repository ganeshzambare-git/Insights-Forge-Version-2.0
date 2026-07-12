# Insight Forge Version 2.0

Insight Forge is a full-stack educational decision intelligence platform with a FastAPI backend and a Next.js frontend.

---

## 📋 Prerequisites

Before running the project, ensure you have:

- Python 3.13+
- Node.js 20+
- npm
- Git

---

## ✨ Key Features

- AI-powered decision intelligence platform.
- FastAPI backend with modular architecture.
- Next.js frontend with enterprise-grade component structure.
- SQLAlchemy ORM with database migrations.
- Environment-based configuration for development and production.
- Scalable project structure for future feature expansion.

---

## Repository Layout

- `insight-forge-backend/` - FastAPI application, SQLAlchemy models, migrations, services, tests, and operational scripts.
- `insight-forge-frontend/` - Next.js React frontend organized by enterprise feature domains.
- `database/`, `docs/`, and `workflows/` content live under the backend and root workflow folders.
- `brain/` contains project architecture, roadmap, patterns, and implementation memory.
- ### Components

- **Backend:** REST APIs, business logic, authentication, database models.
- **Frontend:** Dashboard, analytics, reports, and visualization interface.
- **Brain:** Architecture documentation, implementation notes, and roadmap.

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

---

## 🚀 Future Roadmap

- AI-powered predictive analytics
- Real-time dashboard updates
- Multi-language support
- Docker & Kubernetes deployment
- Advanced reporting and export functionality

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes with clear commit messages.
4. Open a Pull Request for review.

"""
Insight Forge V2 — V1 API Root Router.

Consolidates and registers all V1 resource endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    cohorts,
    datasets,
    finance,
    health,
    ingestion,
    interventions,
    metrics,
    reports,
    tasks,
    tenants,
    users,
    ai,
    cleaning,
    admin,
    ingest,
    simulations,
    student,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tenants.router)
api_router.include_router(tenants.public_router)
api_router.include_router(cohorts.router)
api_router.include_router(datasets.router)
api_router.include_router(ingestion.router)
api_router.include_router(interventions.router)
api_router.include_router(metrics.router)
api_router.include_router(reports.router)
api_router.include_router(analytics.router)
api_router.include_router(health.router)
api_router.include_router(ai.router)
api_router.include_router(cleaning.router)
api_router.include_router(admin.router)
api_router.include_router(ingest.router)
api_router.include_router(simulations.router)
api_router.include_router(student.router)
api_router.include_router(finance.router)
api_router.include_router(tasks.router)



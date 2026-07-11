"""
Insight Forge V2 — Finance Service.

Builds the tenant resource-allocation dashboard from real ``budget_allocations``
rows: the budget ledger, utilization KPI cards, and a financial summary.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.models.budget_allocation import BudgetAllocation
from app.repositories.budget_allocation import BudgetAllocationRepository
from app.services.audit import AuditLoggerProtocol
from app.services.base import BaseService
from app.services.context import ServiceContext
from app.services.providers import ClockProvider, UUIDProvider
from app.services.result import ServiceResult
from app.services.uow import UnitOfWork


class FinanceService(BaseService):
    """Business service governing budget allocations and utilization reporting."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        super().__init__(uow, context, audit_logger, clock, uuid_provider)
        self.repo = BudgetAllocationRepository(session=uow.session)

    async def create_allocation(
        self,
        tenant_id: uuid.UUID,
        category: str,
        description: str,
        dimension: str,
        fiscal_year: str,
        allocated_budget: Decimal,
        current_balance: Decimal,
    ) -> ServiceResult[BudgetAllocation]:
        """Create a budget allocation line for a tenant."""

        async def action() -> BudgetAllocation:
            allocation = BudgetAllocation(
                allocation_id=self.uuid_provider.generate(),
                tenant_id=tenant_id,
                category=category,
                description=description,
                dimension=dimension,
                fiscal_year=fiscal_year,
                allocated_budget=allocated_budget,
                current_balance=current_balance,
            )
            return await self.repo.create(allocation)

        return await self.execute_command(
            "create_allocation", action, success_msg="Budget allocation created."
        )

    async def resource_allocation(
        self, tenant_id: uuid.UUID, dimension: str | None = None
    ) -> dict[str, Any]:
        """Assemble the finance dashboard payload from real allocations."""
        rows = await self.repo.list_for_tenant(tenant_id, dimension=dimension)

        ledger: list[dict[str, Any]] = []
        for r in rows:
            allocated = float(r.allocated_budget)
            balance = float(r.current_balance)
            spent = allocated - balance
            utilization = round((spent / allocated) * 100, 2) if allocated else 0.0
            ledger.append(
                {
                    "allocation_id": str(r.allocation_id),
                    "category": r.category,
                    "description": r.description,
                    "allocated_budget": allocated,
                    "current_balance": balance,
                    "utilization_pct": utilization,
                    "fiscal_year": r.fiscal_year,
                    "dimension": r.dimension,
                }
            )

        total_allocated = sum(item["allocated_budget"] for item in ledger)
        total_balance = sum(item["current_balance"] for item in ledger)
        total_spent = total_allocated - total_balance
        overall_util = (
            round((total_spent / total_allocated) * 100, 2) if total_allocated else 0.0
        )
        fiscal_year = ledger[0]["fiscal_year"] if ledger else "FY-2026"

        utilization_cards = [
            {"label": "Total Allocated", "value": f"${total_allocated:,.2f}", "icon": "", "color": "#38bdf8"},
            {"label": "Current Balance", "value": f"${total_balance:,.2f}", "icon": "", "color": "#34d399"},
            {"label": "Total Spent", "value": f"${total_spent:,.2f}", "icon": "", "color": "#f59e0b"},
            {"label": "Overall Utilization", "value": f"{overall_util}%", "icon": "", "color": "#a78bfa"},
        ]

        return {
            "budget_ledger": ledger,
            "utilization_cards": utilization_cards,
            "financial_summary": {
                "total_allocated": total_allocated,
                "total_balance": total_balance,
                "total_spent": total_spent,
                "overall_utilization_pct": overall_util,
                "fiscal_year": fiscal_year,
                "tenant_id": str(tenant_id),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "filters_applied": {"dimension": dimension},
        }

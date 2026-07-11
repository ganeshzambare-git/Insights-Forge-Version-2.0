"""
Insight Forge V2 — Budget Allocation Model.

Tenant-scoped financial allocations powering the finance/resource-allocation
dashboard. Utilization is derived from allocated vs. current balance.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins.timestamp import TimestampMixin


class BudgetAllocation(Base, TimestampMixin):
    """A single budget line for a tenant (category / dimension / fiscal year)."""

    __tablename__ = "budget_allocations"

    allocation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    dimension: Mapped[str] = mapped_column(String(128), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(16), nullable=False)

    allocated_budget: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2), nullable=False
    )

"""
Insight Forge V2 — Demo Data Seeder.

Populates the default tenant with realistic academic data so the analytics
dashboards render real numbers: cohorts, student users, student metrics across
three reporting periods, and a few coaching interventions.

Idempotent: if student metrics already exist for the tenant, it exits without
duplicating data.

Run:  python scripts/seed_demo_data.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from decimal import Decimal
from pathlib import Path

# Allow "python scripts/seed_demo_data.py" from the backend root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import async_session_maker  # noqa: E402
from app.models.budget_allocation import BudgetAllocation  # noqa: E402
from app.models.cohort import Cohort  # noqa: E402
from app.models.coaching_intervention import CoachingIntervention  # noqa: E402
from app.models.student_metric import StudentMetric  # noqa: E402
from app.models.user import User  # noqa: E402

BUDGET_LINES = [
    ("Infrastructure", "Cloud compute cluster reservation", "Technology", 120000, 84300),
    ("Faculty Resources", "Academic staff compensation fund", "Academic", 540000, 412000),
    ("Student Services", "Counselling, tutoring and welfare", "Student Affairs", 95000, 61250),
    ("Research & Development", "Applied AI research grants", "Research", 210000, 178500),
]

REPORTING_PERIODS = ["Spring 2026", "Summer 2026", "Fall 2026"]

COHORTS = [
    ("CS-2026", "Computer Science"),
    ("MTH-2026", "Mathematics"),
    ("ENG-2026", "Engineering"),
]

FIRST_NAMES = [
    "aisha", "ben", "chloe", "dev", "ella", "farid", "grace", "hiro",
    "isla", "james",
]
LAST_NAMES = [
    "khan", "torres", "mensah", "patel", "olsen", "nguyen", "rossi",
    "silva", "adeyemi", "walsh",
]

STUDENT_PASSWORD = "StudentPass123!"


def _risk_status(grade: float, attendance: float) -> str:
    if grade < 60 or attendance < 70:
        return "Critical"
    if grade < 75 or attendance < 85:
        return "Amber"
    return "Safe"


async def seed() -> None:
    async with async_session_maker() as session:
        tenant_id = (
            await session.execute(text("SELECT tenant_id FROM tenants LIMIT 1"))
        ).scalar_one_or_none()
        if not tenant_id:
            print("No tenant found — create a tenant first (bootstrap).")
            return
        tenant_id = uuid.UUID(str(tenant_id))

        # Scope the whole session to this tenant so RLS permits writes/reads.
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, false)"),
            {"t": str(tenant_id)},
        )

        # ---- Finance (independent of academic seed) ----
        budgets = (
            await session.execute(
                text("SELECT count(*) FROM budget_allocations WHERE tenant_id = :t"),
                {"t": str(tenant_id)},
            )
        ).scalar_one()
        if not budgets or int(budgets) == 0:
            for category, desc, dimension, allocated, balance in BUDGET_LINES:
                session.add(
                    BudgetAllocation(
                        allocation_id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        category=category,
                        description=desc,
                        dimension=dimension,
                        fiscal_year="FY-2026",
                        allocated_budget=Decimal(str(allocated)),
                        current_balance=Decimal(str(balance)),
                    )
                )
            await session.commit()
            print(f"Seeded {len(BUDGET_LINES)} budget allocations.")
        else:
            print(f"Budget allocations already present ({budgets}); skipping finance seed.")

        existing = (
            await session.execute(
                text("SELECT count(*) FROM student_metrics WHERE tenant_id = :t"),
                {"t": str(tenant_id)},
            )
        ).scalar_one()
        if existing and int(existing) > 0:
            print(f"Student metrics already present ({existing}); skipping academic seed.")
            return

        faculty_id = (
            await session.execute(
                text(
                    "SELECT user_id FROM users WHERE tenant_id = :t "
                    "AND assigned_role IN ('Faculty','Admin','Dean') LIMIT 1"
                ),
                {"t": str(tenant_id)},
            )
        ).scalar_one_or_none()

        pw_hash = hash_password(STUDENT_PASSWORD)
        created_cohorts = 0
        created_students = 0
        created_metrics = 0
        interventions: list[tuple[uuid.UUID, uuid.UUID]] = []

        for c_index, (code, dept) in enumerate(COHORTS):
            cohort = Cohort(
                cohort_id=uuid.uuid4(),
                tenant_id=tenant_id,
                cohort_code=code,
                department_scope=dept,
            )
            session.add(cohort)
            await session.flush()
            created_cohorts += 1

            for s_index in range(10):
                first = FIRST_NAMES[s_index]
                last = LAST_NAMES[(s_index + c_index) % len(LAST_NAMES)]
                email = f"{first}.{last}{c_index}{s_index}@default.edu"

                student = User(
                    user_id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    corporate_email=email,
                    password_hash=pw_hash,
                    assigned_role="Student",
                    is_mfa_enabled=False,
                )
                session.add(student)
                await session.flush()
                created_students += 1

                # Base performance varies by student; improves each period.
                base_grade = 58 + (s_index * 4) + (c_index * 2)  # 58..~100
                base_attend = 70 + (s_index * 2) + (c_index * 1)
                for p_index, period in enumerate(REPORTING_PERIODS):
                    grade = min(100.0, base_grade + p_index * 3)
                    attend = min(100.0, base_attend + p_index * 4)
                    metric = StudentMetric(
                        tenant_id=tenant_id,
                        student_user_id=student.user_id,
                        cohort_id=cohort.cohort_id,
                        raw_average_grade=Decimal(str(round(grade, 2))),
                        normalized_grade_score=Decimal(str(round(grade, 2))),
                        attendance_percentage=Decimal(str(round(attend, 2))),
                        success_indicator_status=_risk_status(grade, attend),
                        reporting_period=period,
                    )
                    session.add(metric)
                    created_metrics += 1

                # Flag the weakest student in each cohort for coaching.
                if faculty_id and s_index == 0:
                    interventions.append((student.user_id, uuid.UUID(str(faculty_id))))

        for student_uid, fac_uid in interventions:
            session.add(
                CoachingIntervention(
                    intervention_id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    student_user_id=student_uid,
                    faculty_user_id=fac_uid,
                    intervention_notes="Initial academic risk review and support plan.",
                )
            )

        await session.commit()
        print(
            f"Seeded: {created_cohorts} cohorts, {created_students} students, "
            f"{created_metrics} metrics, {len(interventions)} interventions "
            f"(student password: {STUDENT_PASSWORD})."
        )


if __name__ == "__main__":
    asyncio.run(seed())

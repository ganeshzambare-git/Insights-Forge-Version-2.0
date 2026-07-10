"""
Insight Forge V2 — Analytics Service.

Centralizes academic intelligence logic, KPI aggregations, and rule-based risk engines.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
from typing import Any
from sqlalchemy import select, func, and_, case

from app.models.user import User
from app.models.cohort import Cohort
from app.models.student_metric import StudentMetric
from app.models.coaching_intervention import CoachingIntervention
from app.services.base import BaseService
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider
from app.api.v1.schemas.analytics import (
    DashboardOverviewResponse,
    KPIResponse,
    StudentRiskResponse,
    TrendResponse,
    MetricTrendItem,
    InterventionTrendItem,
    RecommendationResponse,
    CohortAnalyticsResponse,
    FacultyAnalyticsResponse,
    InstitutionAnalyticsResponse,
    DepartmentComparisonItem,
)


class AnalyticsService(BaseService):
    """Business service governing academic intelligence computations."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        super().__init__(uow, context, audit_logger, clock, uuid_provider)

    async def get_dashboard(self, tenant_id: uuid.UUID) -> DashboardOverviewResponse:
        """Aggregate high-level overview dashboard statistics."""
        # 1. Total counts
        students_count = await self._get_user_count_by_role(tenant_id, "Student")
        faculty_count = await self._get_user_count_by_role(tenant_id, "Faculty")

        cohorts_count = (
            await self.uow.session.scalar(
                select(func.count(Cohort.cohort_id)).where(
                    Cohort.tenant_id == tenant_id
                )
            )
            or 0
        )

        interventions_count = (
            await self.uow.session.scalar(
                select(func.count(CoachingIntervention.intervention_id)).where(
                    CoachingIntervention.tenant_id == tenant_id
                )
            )
            or 0
        )

        # 2. Risk evaluation of active students
        student_profiles = await self._get_student_profiles_with_metrics(tenant_id)
        critical_count = 0
        amber_count = 0
        safe_count = 0
        total_gpa = 0.0
        total_attendance = 0.0
        students_with_metrics = 0

        for profile in student_profiles:
            risk = self._classify_risk(
                gpa=profile["gpa"],
                attendance=profile["attendance"],
                critical_interventions=profile["critical_interventions"],
            )
            if risk == "Critical":
                critical_count += 1
            elif risk == "Amber":
                amber_count += 1
            else:
                safe_count += 1

            if profile["gpa"] is not None and profile["attendance"] is not None:
                total_gpa += float(profile["gpa"])
                total_attendance += float(profile["attendance"])
                students_with_metrics += 1

        avg_gpa = (
            (total_gpa / students_with_metrics) if students_with_metrics > 0 else 0.0
        )
        avg_attendance = (
            (total_attendance / students_with_metrics)
            if students_with_metrics > 0
            else 0.0
        )

        return DashboardOverviewResponse(
            total_students=students_count,
            total_faculty=faculty_count,
            total_cohorts=cohorts_count,
            average_gpa=round(avg_gpa, 2),
            average_attendance=round(avg_attendance, 2),
            critical_students=critical_count,
            amber_students=amber_count,
            safe_students=safe_count,
            total_interventions=interventions_count,
        )

    async def get_kpis(self, tenant_id: uuid.UUID) -> KPIResponse:
        """Fetch count key performance indicators for users."""
        roles_query = await self.uow.session.execute(
            select(User.assigned_role, func.count(User.user_id))
            .where(User.tenant_id == tenant_id)
            .group_by(User.assigned_role)
        )
        counts = {r: count for r, count in roles_query.all()}

        total = sum(counts.values())
        return KPIResponse(
            total_users=total,
            active_faculty=counts.get("Faculty", 0),
            active_students=counts.get("Student", 0),
            active_deans=counts.get("Dean", 0),
        )

    async def get_student_risk(
        self,
        tenant_id: uuid.UUID,
        cohort_id: uuid.UUID | None = None,
        risk_level: str | None = None,
    ) -> list[StudentRiskResponse]:
        """Classify student risk dynamically with filters."""
        profiles = await self._get_student_profiles_with_metrics(tenant_id)
        results = []

        for p in profiles:
            # Filter by Cohort ID if provided
            if cohort_id and p["cohort_id"] != cohort_id:
                continue

            risk = self._classify_risk(
                gpa=p["gpa"],
                attendance=p["attendance"],
                critical_interventions=p["critical_interventions"],
            )

            # Filter by Risk Level if provided
            if risk_level and risk.lower() != risk_level.lower():
                continue

            results.append(
                StudentRiskResponse(
                    student_id=p["user_id"],
                    student_email=p["corporate_email"],
                    gpa=float(p["gpa"]) if p["gpa"] is not None else None,
                    attendance_rate=(
                        float(p["attendance"]) if p["attendance"] is not None else None
                    ),
                    risk_level=risk,
                    intervention_count=p["total_interventions"],
                )
            )

        return results

    async def get_trends(self, tenant_id: uuid.UUID) -> TrendResponse:
        """Fetch metrics terms history and interventions calendar counts."""
        # 1. Metrics aggregated by reporting period term
        metrics_query = await self.uow.session.execute(
            select(
                StudentMetric.reporting_period,
                func.avg(StudentMetric.raw_average_grade).label("avg_gpa"),
                func.avg(StudentMetric.attendance_percentage).label("avg_att"),
            )
            .where(StudentMetric.tenant_id == tenant_id)
            .group_by(StudentMetric.reporting_period)
            .order_by(StudentMetric.reporting_period)
        )

        metrics_trend = [
            MetricTrendItem(
                reporting_period=row.reporting_period,
                average_gpa=round(float(row.avg_gpa), 2),
                average_attendance=round(float(row.avg_att), 2),
            )
            for row in metrics_query.all()
        ]

        # 2. Interventions grouped by calendar windows
        now = datetime.now(timezone.utc)
        days_7 = now - timedelta(days=7)
        days_30 = now - timedelta(days=30)
        days_90 = now - timedelta(days=90)

        counts_query = await self.uow.session.execute(
            select(
                func.count(
                    case((CoachingIntervention.recorded_timestamp >= days_7, 1))
                ).label("count_7"),
                func.count(
                    case((CoachingIntervention.recorded_timestamp >= days_30, 1))
                ).label("count_30"),
                func.count(
                    case((CoachingIntervention.recorded_timestamp >= days_90, 1))
                ).label("count_90"),
            ).where(CoachingIntervention.tenant_id == tenant_id)
        )
        row = counts_query.one()

        interventions_trend = [
            InterventionTrendItem(timeframe="Last 7 Days", count=row.count_7 or 0),
            InterventionTrendItem(timeframe="Last 30 Days", count=row.count_30 or 0),
            InterventionTrendItem(timeframe="Last 90 Days", count=row.count_90 or 0),
        ]

        return TrendResponse(
            metrics_trend=metrics_trend,
            interventions_trend=interventions_trend,
        )

    async def get_recommendations(
        self, tenant_id: uuid.UUID
    ) -> list[RecommendationResponse]:
        """Trigger deterministic rule-based recommendations for students at risk."""
        profiles = await self._get_student_profiles_with_metrics(tenant_id)
        recommendations = []
        now = datetime.now(timezone.utc)

        for p in profiles:
            gpa = p["gpa"]
            attendance = p["attendance"]
            risk = self._classify_risk(
                gpa=gpa,
                attendance=attendance,
                critical_interventions=p["critical_interventions"],
            )

            # Rule 1: GPA checks
            if gpa is not None:
                if gpa < Decimal("60.00"):
                    recommendations.append(
                        RecommendationResponse(
                            student_id=p["user_id"],
                            student_email=p["corporate_email"],
                            rule_name="CRITICAL_GPA",
                            recommendation_text="GPA is critically low. Schedule academic counselling.",
                            severity="High",
                        )
                    )
                elif gpa < Decimal("75.00"):
                    recommendations.append(
                        RecommendationResponse(
                            student_id=p["user_id"],
                            student_email=p["corporate_email"],
                            rule_name="LOW_GPA",
                            recommendation_text="GPA is below standard. Recommend academic coaching.",
                            severity="Medium",
                        )
                    )

            # Rule 2: Attendance checks
            if attendance is not None:
                if attendance < Decimal("75.00"):
                    recommendations.append(
                        RecommendationResponse(
                            student_id=p["user_id"],
                            student_email=p["corporate_email"],
                            rule_name="CRITICAL_ATTENDANCE",
                            recommendation_text="Attendance rate is critical. Schedule parent/dean meeting.",
                            severity="High",
                        )
                    )
                elif attendance < Decimal("85.00"):
                    recommendations.append(
                        RecommendationResponse(
                            student_id=p["user_id"],
                            student_email=p["corporate_email"],
                            rule_name="LOW_ATTENDANCE",
                            recommendation_text="Attendance drop detected. Faculty consultation recommended.",
                            severity="Medium",
                        )
                    )

            # Rule 3: Critical risk review
            if risk == "Critical":
                recommendations.append(
                    RecommendationResponse(
                        student_id=p["user_id"],
                        student_email=p["corporate_email"],
                        rule_name="DEAN_REVIEW",
                        recommendation_text="Critical risk profile. Flagged for immediate Dean review.",
                        severity="High",
                    )
                )

            # Rule 4: Intervention gap
            latest_time = p["latest_intervention_time"]
            if (risk in ("Amber", "Critical")) and (
                latest_time is None or (now - latest_time) > timedelta(days=60)
            ):
                recommendations.append(
                    RecommendationResponse(
                        student_id=p["user_id"],
                        student_email=p["corporate_email"],
                        rule_name="INTERVENTION_LAPSE",
                        recommendation_text="No intervention logged in last 60 days. Faculty follow-up required.",
                        severity="Medium",
                    )
                )

        return recommendations

    async def get_cohort_performance(
        self, tenant_id: uuid.UUID
    ) -> list[CohortAnalyticsResponse]:
        """Aggregate cohort averages and risk breakdowns."""
        cohorts_query = await self.uow.session.execute(
            select(Cohort).where(Cohort.tenant_id == tenant_id)
        )
        cohorts = cohorts_query.scalars().all()

        profiles = await self._get_student_profiles_with_metrics(tenant_id)
        results = []

        for c in cohorts:
            cohort_profiles = [p for p in profiles if p["cohort_id"] == c.cohort_id]
            student_count = len(cohort_profiles)

            total_gpa = 0.0
            total_attendance = 0.0
            metrics_count = 0
            critical = 0
            amber = 0
            safe = 0

            for p in cohort_profiles:
                risk = self._classify_risk(
                    gpa=p["gpa"],
                    attendance=p["attendance"],
                    critical_interventions=p["critical_interventions"],
                )
                if risk == "Critical":
                    critical += 1
                elif risk == "Amber":
                    amber += 1
                else:
                    safe += 1

                if p["gpa"] is not None and p["attendance"] is not None:
                    total_gpa += float(p["gpa"])
                    total_attendance += float(p["attendance"])
                    metrics_count += 1

            avg_gpa = (total_gpa / metrics_count) if metrics_count > 0 else 0.0
            avg_attendance = (
                (total_attendance / metrics_count) if metrics_count > 0 else 0.0
            )

            results.append(
                CohortAnalyticsResponse(
                    cohort_id=c.cohort_id,
                    cohort_code=c.cohort_code,
                    department_scope=c.department_scope,
                    average_gpa=round(avg_gpa, 2),
                    average_attendance=round(avg_attendance, 2),
                    student_count=student_count,
                    critical_count=critical,
                    amber_count=amber,
                    safe_count=safe,
                )
            )

        return results

    async def get_faculty_performance(
        self, tenant_id: uuid.UUID
    ) -> list[FacultyAnalyticsResponse]:
        """Fetch workload counts and student improvements grouped by advisor/faculty."""
        # 1. Get faculty users
        faculty_query = await self.uow.session.execute(
            select(User).where(
                and_(User.tenant_id == tenant_id, User.assigned_role == "Faculty")
            )
        )
        faculty_members = faculty_query.scalars().all()

        # 2. Get all interventions
        interventions_query = await self.uow.session.execute(
            select(CoachingIntervention).where(
                CoachingIntervention.tenant_id == tenant_id
            )
        )
        interventions = interventions_query.scalars().all()

        # 3. Get all student metrics to compute improvements
        metrics_query = await self.uow.session.execute(
            select(StudentMetric)
            .where(StudentMetric.tenant_id == tenant_id)
            .order_by(StudentMetric.metric_id)
        )
        all_metrics = metrics_query.scalars().all()

        # Group metrics by student
        student_metrics_map = {}
        for m in all_metrics:
            student_metrics_map.setdefault(m.student_user_id, []).append(m)

        results = []
        for f in faculty_members:
            f_interventions = [
                i for i in interventions if i.faculty_user_id == f.user_id
            ]
            unique_students = {i.student_user_id for i in f_interventions}

            total_improvement = 0.0
            improvement_count = 0

            for s_id in unique_students:
                s_metrics = student_metrics_map.get(s_id, [])
                if len(s_metrics) >= 2:
                    first_gpa = float(s_metrics[0].raw_average_grade)
                    last_gpa = float(s_metrics[-1].raw_average_grade)
                    total_improvement += last_gpa - first_gpa
                    improvement_count += 1

            avg_improvement = (
                (total_improvement / improvement_count)
                if improvement_count > 0
                else 0.0
            )

            results.append(
                FacultyAnalyticsResponse(
                    faculty_id=f.user_id,
                    faculty_email=f.corporate_email,
                    students_managed=len(unique_students),
                    interventions_logged=len(f_interventions),
                    average_improvement=round(avg_improvement, 2),
                )
            )

        return results

    async def get_institution_health(
        self, tenant_id: uuid.UUID
    ) -> InstitutionAnalyticsResponse:
        """Calculate high-level overall institutional health indices."""
        dashboard = await self.get_dashboard(tenant_id)
        total = dashboard.total_students

        # Health score: Safe * 100 + Amber * 60 + Critical * 10
        overall_health = 100.0
        if total > 0:
            weighted = (
                dashboard.safe_students * 1.0
                + dashboard.amber_students * 0.6
                + dashboard.critical_students * 0.1
            )
            overall_health = (weighted / total) * 100.0

        # Department breakdown comparison
        cohorts_perf = await self.get_cohort_performance(tenant_id)
        dept_map = {}
        for cp in cohorts_perf:
            dept = cp.department_scope
            dept_map.setdefault(dept, []).append(cp)

        department_comparison = []
        for dept, cp_list in dept_map.items():
            dept_students = sum(cp.student_count for cp in cp_list)
            dept_gpa = sum(cp.average_gpa * cp.student_count for cp in cp_list)
            dept_att = sum(cp.average_attendance * cp.student_count for cp in cp_list)

            avg_gpa = (dept_gpa / dept_students) if dept_students > 0 else 0.0
            avg_att = (dept_att / dept_students) if dept_students > 0 else 0.0

            department_comparison.append(
                DepartmentComparisonItem(
                    department=dept,
                    average_gpa=round(avg_gpa, 2),
                    average_attendance=round(avg_att, 2),
                    student_count=dept_students,
                )
            )

        return InstitutionAnalyticsResponse(
            overall_health_score=round(overall_health, 2),
            average_gpa=dashboard.average_gpa,
            average_attendance=dashboard.average_attendance,
            risk_distribution={
                "Safe": dashboard.safe_students,
                "Amber": dashboard.amber_students,
                "Critical": dashboard.critical_students,
            },
            department_comparison=department_comparison,
        )

    # ============================================================
    # PRIVATE UTILITIES & HELPERS
    # ============================================================

    async def _get_user_count_by_role(self, tenant_id: uuid.UUID, role: str) -> int:
        """Count users belonging to a tenant filtered by role."""
        return (
            await self.uow.session.scalar(
                select(func.count(User.user_id)).where(
                    and_(User.tenant_id == tenant_id, User.assigned_role == role)
                )
            )
            or 0
        )

    async def _get_student_profiles_with_metrics(
        self, tenant_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Fetch all students latest metrics and critical intervention counts.

        Prevents N+1 query structures.
        """
        # 1. Latest metric subquery
        subq = (
            select(
                StudentMetric.student_user_id,
                func.max(StudentMetric.metric_id).label("max_id"),
            )
            .where(StudentMetric.tenant_id == tenant_id)
            .group_by(StudentMetric.student_user_id)
            .subquery()
        )

        # 2. Critical interventions subquery (Notes carrying "critical" case-insensitive)
        crit_subq = (
            select(
                CoachingIntervention.student_user_id,
                func.count(CoachingIntervention.intervention_id).label("crit_count"),
                func.max(CoachingIntervention.recorded_timestamp).label("latest_time"),
            )
            .where(
                and_(
                    CoachingIntervention.tenant_id == tenant_id,
                    func.lower(CoachingIntervention.intervention_notes).like(
                        "%critical%"
                    ),
                )
            )
            .group_by(CoachingIntervention.student_user_id)
            .subquery()
        )

        # 3. Total interventions subquery
        tot_subq = (
            select(
                CoachingIntervention.student_user_id,
                func.count(CoachingIntervention.intervention_id).label("total_count"),
            )
            .where(CoachingIntervention.tenant_id == tenant_id)
            .group_by(CoachingIntervention.student_user_id)
            .subquery()
        )

        # 4. Main Query
        query = (
            select(
                User.user_id,
                User.corporate_email,
                StudentMetric.cohort_id,
                StudentMetric.raw_average_grade.label("gpa"),
                StudentMetric.attendance_percentage.label("attendance"),
                func.coalesce(crit_subq.c.crit_count, 0).label("crit_count"),
                func.coalesce(tot_subq.c.total_count, 0).label("total_count"),
                crit_subq.c.latest_time,
            )
            .select_from(User)
            .outerjoin(subq, User.user_id == subq.c.student_user_id)
            .outerjoin(
                StudentMetric,
                and_(
                    StudentMetric.student_user_id == subq.c.student_user_id,
                    StudentMetric.metric_id == subq.c.max_id,
                ),
            )
            .outerjoin(crit_subq, User.user_id == crit_subq.c.student_user_id)
            .outerjoin(tot_subq, User.user_id == tot_subq.c.student_user_id)
            .where(
                and_(
                    User.tenant_id == tenant_id,
                    User.assigned_role == "Student",
                )
            )
        )

        result = await self.uow.session.execute(query)
        profiles = []
        for row in result.all():
            profiles.append(
                {
                    "user_id": row.user_id,
                    "corporate_email": row.corporate_email,
                    "cohort_id": row.cohort_id,
                    "gpa": row.gpa,
                    "attendance": row.attendance,
                    "critical_interventions": row.crit_count,
                    "total_interventions": row.total_count,
                    "latest_intervention_time": row.latest_time,
                }
            )

        return profiles

    def _classify_risk(
        self,
        gpa: Decimal | None,
        attendance: Decimal | None,
        critical_interventions: int,
    ) -> str:
        """Dynamic risk rules execution."""
        # Defaults to safe if no metrics recorded
        if gpa is None or attendance is None:
            return "Safe"

        # Critical
        if (
            gpa < Decimal("60.00")
            or attendance < Decimal("75.00")
            or critical_interventions >= 3
        ):
            return "Critical"

        # Amber
        if (
            gpa < Decimal("75.00")
            or attendance < Decimal("85.00")
            or critical_interventions >= 1
        ):
            return "Amber"

        # Safe
        return "Safe"

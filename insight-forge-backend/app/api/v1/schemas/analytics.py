"""
Insight Forge V2 — Analytics DTO Schemas.

Defines Pydantic request and response models for Business Intelligence / Analytics endpoints.
"""

import uuid
from pydantic import BaseModel, Field


class DashboardOverviewResponse(BaseModel):
    """Schema representing dashboard summary statistics."""

    total_students: int = Field(
        ..., description="Total student accounts inside the partition."
    )
    total_faculty: int = Field(
        ..., description="Total faculty accounts inside the partition."
    )
    total_cohorts: int = Field(..., description="Total academic cohorts.")
    average_gpa: float = Field(..., description="Average institutional GPA score.")
    average_attendance: float = Field(
        ..., description="Average institutional attendance rate."
    )
    critical_students: int = Field(
        ..., description="Count of students flagged as Critical risk."
    )
    amber_students: int = Field(
        ..., description="Count of students flagged as Amber risk."
    )
    safe_students: int = Field(..., description="Count of students flagged as Safe.")
    total_interventions: int = Field(
        ..., description="Total logged coaching sessions count."
    )


class KPIResponse(BaseModel):
    """Schema representing user count key performance indicators."""

    total_users: int = Field(..., description="Total registered accounts.")
    active_faculty: int = Field(..., description="Count of Faculty members.")
    active_students: int = Field(..., description="Count of Student members.")
    active_deans: int = Field(..., description="Count of Dean members.")


class StudentRiskResponse(BaseModel):
    """Schema representing dynamic risk classification payload of a student."""

    student_id: uuid.UUID = Field(
        ..., description="Unique UUID primary key of the student user."
    )
    student_email: str = Field(
        ..., description="Corporate email address of the student."
    )
    gpa: float | None = Field(None, description="Latest logged cumulative GPA.")
    attendance_rate: float | None = Field(
        None, description="Latest logged attendance percentage."
    )
    risk_level: str = Field(
        ..., description="Calculated risk classification level (Safe, Amber, Critical)."
    )
    intervention_count: int = Field(
        ..., description="Total interventions logged for the student."
    )


class MetricTrendItem(BaseModel):
    """Trend item representing performance aggregated over a reporting period."""

    reporting_period: str = Field(
        ..., description="Term indicator period (e.g. 2025-S1)."
    )
    average_gpa: float = Field(..., description="Period average GPA score.")
    average_attendance: float = Field(
        ..., description="Period average attendance rate."
    )


class InterventionTrendItem(BaseModel):
    """Trend item representing intervention count over a calendar timeframe."""

    timeframe: str = Field(
        ..., description="Calendar interval window (e.g. Last 7 Days)."
    )
    count: int = Field(..., description="Total interventions count logged.")


class TrendResponse(BaseModel):
    """Schema representing multi-series academic and intervention trend payload."""

    metrics_trend: list[MetricTrendItem] = Field(
        ..., description="Student metrics grouped by reporting term."
    )
    interventions_trend: list[InterventionTrendItem] = Field(
        ..., description="Intervention counts by calendar timeframes."
    )


class RecommendationResponse(BaseModel):
    """Schema representing rule-based academic advisory recommendation flags."""

    student_id: uuid.UUID = Field(..., description="Student UUID context.")
    student_email: str = Field(..., description="Student corporate email address.")
    rule_name: str = Field(..., description="Triggered rule identifier code.")
    recommendation_text: str = Field(..., description="Advisory remediation text.")
    severity: str = Field(
        ..., description="Remediation severity indicator (Low, Medium, High)."
    )


class CohortAnalyticsResponse(BaseModel):
    """Schema representing aggregated metrics comparing academic cohorts."""

    cohort_id: uuid.UUID = Field(..., description="Cohort UUID.")
    cohort_code: str = Field(..., description="Unique cohort code.")
    department_scope: str = Field(..., description="Department scope or program scope.")
    average_gpa: float = Field(..., description="Cohort average GPA grade.")
    average_attendance: float = Field(
        ..., description="Cohort average attendance percentage."
    )
    student_count: int = Field(..., description="Cohort total student population.")
    critical_count: int = Field(
        ..., description="Count of critical risk students inside cohort."
    )
    amber_count: int = Field(
        ..., description="Count of amber risk students inside cohort."
    )
    safe_count: int = Field(..., description="Count of safe students inside cohort.")


class FacultyAnalyticsResponse(BaseModel):
    """Schema representing workload and performance analytics of an advisor."""

    faculty_id: uuid.UUID = Field(..., description="Faculty user UUID.")
    faculty_email: str = Field(..., description="Faculty corporate email.")
    students_managed: int = Field(
        ..., description="Count of students managed or intervened."
    )
    interventions_logged: int = Field(
        ..., description="Total interventions logged by faculty."
    )
    average_improvement: float = Field(
        ..., description="Average student improvement delta."
    )


class DepartmentComparisonItem(BaseModel):
    """Comparison item for department scope performance indicators."""

    department: str = Field(..., description="Department scope name.")
    average_gpa: float = Field(..., description="Department average GPA.")
    average_attendance: float = Field(..., description="Department average attendance.")
    student_count: int = Field(..., description="Total student count.")


class InstitutionAnalyticsResponse(BaseModel):
    """Schema representing high-level overall institutional health indices."""

    overall_health_score: float = Field(
        ..., description="Calculated institutional health score index (0-100)."
    )
    average_gpa: float = Field(..., description="Institution average GPA.")
    average_attendance: float = Field(
        ..., description="Institution average attendance."
    )
    risk_distribution: dict[str, int] = Field(
        ..., description="Total counts grouped by risk level."
    )
    department_comparison: list[DepartmentComparisonItem] = Field(
        ..., description="Breakdown comparisons of departments."
    )

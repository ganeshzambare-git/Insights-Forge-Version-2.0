"""
Insight Forge V2 — Academic Mapping Helpers.

Pure functions that translate stored ``student_metrics`` fields into the
presentation shapes the dashboards expect (GPA on a 4.0 scale, letter grades,
and risk tiers). Kept dependency-free so services and tests can reuse them.
"""

from __future__ import annotations

from decimal import Decimal

# success_indicator_status (stored) -> risk label (frontend)
_STATUS_TO_RISK = {
    "Safe": "Low",
    "Amber": "Medium",
    "Critical": "High",
}


def status_to_risk(status: str | None) -> str:
    """Map a stored success indicator to a coarse risk label."""
    return _STATUS_TO_RISK.get(status or "", "Unknown")


def grade_to_gpa(raw_average_grade: Decimal | float | None) -> float:
    """Convert a 0–100 average grade into a 0–4.0 GPA (rounded to 2dp)."""
    if raw_average_grade is None:
        return 0.0
    return round(float(raw_average_grade) / 100.0 * 4.0, 2)


def grade_to_letter(raw_average_grade: Decimal | float | None) -> str:
    """Convert a 0–100 average grade into a letter grade."""
    if raw_average_grade is None:
        return "N/A"
    score = float(raw_average_grade)
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"

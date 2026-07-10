"""
Insight Forge V2 — Executive Report Engine.

Implements C-suite overview text builders, priority rankings, and business health score models in pure Python.
"""

from typing import Any
from app.ai.schemas.executive import ExecutiveFinding, ExecutiveRecommendation, ExecutiveReport
from app.ai.utils.helpers import deduplicate_by_title



def calculate_overall_business_health(
    anomalies: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
) -> float:
    """Calculate overall business health percentage index score (0-100).

    Base starts at 100.0.
    - High/Critical anomalies deduct 10 points.
    - Medium anomalies deduct 5 points.
    - Validate opportunities add 5 bonus points (capped at 100.0).
    """
    score = 100.0

    for a in anomalies:
        sev = str(a.get("severity", "Low")).lower()
        if "critical" in sev or "high" in sev:
            score -= 10.0
        elif "medium" in sev:
            score -= 5.0
        else:
            score -= 2.0

    for o in opportunities:
        roi = o.get("estimated_roi", 0.0)
        if roi >= 200.0:
            score += 5.0
        else:
            score += 2.0

    # Ensure score bounds
    return max(0.0, min(100.0, score))


def generate_executive_summary(
    dataset_name: str,
    anomalies_count: int,
    validated_count: int,
    health_score: float,
) -> str:
    """Compile concise human-readable strategic executive summary text."""
    if health_score >= 85.0:
        health_status = "stable and optimal"
    elif health_score >= 60.0:
        health_status = "moderate, with localized risks requiring intervention"
    else:
        health_status = "critical, requiring immediate engineering and operational audits"

    return (
        f"Executive Summary for '{dataset_name}': The overall database operational profile index is scored "
        f"at {health_score:.1f}% ({health_status}). We identified {anomalies_count} data quality anomalies "
        f"which require review. Concurrently, {validated_count} validated strategic recommendations "
        f"have been formulated to capture cost-reduction and growth opportunities."
    )


def build_executive_report(
    dataset_name: str,
    anomalies: list[dict[str, Any]],
    insights: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    warnings: list[str],
) -> ExecutiveReport:
    """Construct an ExecutiveReport aggregating findings, recommendations, and health scores."""
    # 1. Calculate overall business health score
    health_score = calculate_overall_business_health(anomalies, opportunities)

    # 2. Compile executive summary description text
    summary_text = generate_executive_summary(
        dataset_name, len(anomalies), len(recommendations), health_score
    )

    # 3. Formulate key findings (C-suite view)
    key_findings = []
    # Add anomalies as negative quality findings
    for a in anomalies:
        key_findings.append(
            ExecutiveFinding(
                title=f"Anomaly: {a.get('title')}",
                description=a.get("description", "Quality exception flagged."),
                evidence=a.get("evidence", ""),
                confidence=a.get("confidence", 0.95),
                business_impact=f"High risk anomaly. {a.get('recommendation', '')}",
            )
        )

    # Add validated insights as strategic growth findings
    for i in insights:
        key_findings.append(
            ExecutiveFinding(
                title=f"Insight: {i.get('title')}",
                description=i.get("description", "Significant business driver identified."),
                evidence=i.get("evidence", ""),
                confidence=i.get("confidence", 0.90),
                business_impact=i.get("business_impact", ""),
            )
        )

    # 4. Formulate strategic recommendations
    strategic_recommendations = []
    for r in recommendations:
        strategic_recommendations.append(
            ExecutiveRecommendation(
                title=r.get("title", "Recommendation"),
                priority=r.get("priority", "Medium"),
                estimated_roi=r.get("estimated_roi", 0.0),
                timeline=r.get("timeline", "Short-term"),
                owner=r.get("owner", "Data Team"),
            )
        )

    # Rank recommendations by priority and ROI descending
    priority_order = {"high": 3, "medium": 2, "low": 1}
    strategic_recommendations.sort(
        key=lambda x: (priority_order.get(x.priority.lower(), 0), x.estimated_roi),
        reverse=True,
    )

    key_findings = deduplicate_by_title(key_findings)
    strategic_recommendations = deduplicate_by_title(strategic_recommendations)
    warnings = list(dict.fromkeys(warnings))

    return ExecutiveReport(
        executive_summary=summary_text,
        business_health_score=health_score,
        key_findings=key_findings,
        strategic_recommendations=strategic_recommendations,
        warnings=warnings,
    )

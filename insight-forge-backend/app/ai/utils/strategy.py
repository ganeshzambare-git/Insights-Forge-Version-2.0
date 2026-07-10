"""
Insight Forge V2 — Strategy Engine.

Implements ROI mathematical models, cost-benefit evaluations, risk assessments,
priority rankings, and validated-only recommendation generation in pure Python.
"""

from typing import Any
from app.ai.schemas.strategy import BusinessOpportunity, RiskAssessment, StrategicRecommendation, StrategySummary
from app.ai.utils.helpers import deduplicate_by_title



def calculate_roi(financial_upside: float, execution_cost: float) -> float:
    """Calculate percentage ROI. Returns 0.0 if execution cost is <= 0."""
    if execution_cost <= 0:
        return 0.0
    return ((financial_upside - execution_cost) / execution_cost) * 100.0


def score_priority_by_roi(roi: float, effort: str) -> str:
    """Score priority level (High, Medium, Low) based on ROI scale and effort complexity."""
    if roi >= 500.0 and effort in ["Low", "Medium"]:
        return "High"
    elif roi >= 150.0 and effort != "High":
        return "Medium"
    else:
        return "Low"


def evaluate_strategy_recommendations(
    validated_hypotheses: list[dict[str, Any]],
    rejected_hypotheses: list[dict[str, Any]],
    root_causes: list[dict[str, Any]],
) -> StrategySummary:
    """Synthesize strategic business actions, opportunities, and risk assessments.

    Enforces strict evidence filtering:
    - Recommendations must be backed by validated hypotheses.
    - Growth campaigns are rejected if their supporting organic growth hypotheses are rejected.
    """
    summary = StrategySummary()

    # Track rejected hypotheses to alert/log skipped recommendations
    for rh in rejected_hypotheses:
        title = rh.get("title", "")
        summary.warnings.append(
            f"Recommendation Skipped: Direct action for '{title}' was blocked due to hypothesis rejection."
        )

    # 1. Generate Business Opportunities and Strategic Recommendations from validated hypotheses
    for vh in validated_hypotheses:
        title = vh.get("title", "")
        evidence = vh.get("evidence", "")
        confidence = vh.get("confidence", 0.9)

        if "organic" in title.lower() or "growth" in title.lower():
            # Organic Growth Opportunity
            roi = calculate_roi(150000.0, 50000.0)  # 200% ROI
            summary.opportunities.append(
                BusinessOpportunity(
                    title="Targeted Channel Campaign Scale-up",
                    description="Expand marketing spend and inbound channels to capture validated organic momentum.",
                    priority="High",
                    estimated_roi=roi,
                    business_impact="Increases customer acquisition yield and leverages confirmed market trends.",
                    confidence=confidence,
                    evidence=evidence,
                )
            )
            summary.recommendations.append(
                StrategicRecommendation(
                    title="Deploy Additional Inbound Spend",
                    description="Scale inbound organic growth marketing budget on verified high-performance segments.",
                    priority="High",
                    estimated_roi=roi,
                    business_impact="Captures incremental customer acquisition cohort volumes.",
                    implementation_effort="Medium",
                    timeline="2-4 weeks",
                    owner="Growth Marketing Lead",
                    confidence=confidence,
                    evidence=evidence,
                )
            )

        elif "double-logging" in title.lower() or "ingestion" in title.lower():
            # Technical Duplication Cost Savings
            roi = calculate_roi(80000.0, 10000.0)  # 700% ROI
            summary.opportunities.append(
                BusinessOpportunity(
                    title="ETL Pipeline De-duplication",
                    description="Remediate duplicate database logs and sync server-side validation limits.",
                    priority="High",
                    estimated_roi=roi,
                    business_impact="Saves database storage overhead and repairs corrupted business metrics.",
                    confidence=confidence,
                    evidence=evidence,
                )
            )
            summary.recommendations.append(
                StrategicRecommendation(
                    title="Audit Ingestion Payload De-duplication",
                    description="Implement unique transaction hash indexes on file ingestion pipelines to block duplicates.",
                    priority="High",
                    estimated_roi=roi,
                    business_impact="Eliminates artificial metrics inflation and storage cost overheads.",
                    implementation_effort="Low",
                    timeline="1 week",
                    owner="Data Engineering Lead",
                    confidence=confidence,
                    evidence=evidence,
                )
            )

        elif "cohort" in title.lower() or "segment" in title.lower():
            roi = calculate_roi(120000.0, 30000.0)  # 300% ROI
            summary.opportunities.append(
                BusinessOpportunity(
                    title="Cohort-based Pricing Optimization",
                    description="Tailor price plans and discounts to leverage segment performance gaps.",
                    priority="Medium",
                    estimated_roi=roi,
                    business_impact="Increases cohort margins and custom customer loyalty.",
                    confidence=confidence,
                    evidence=evidence,
                )
            )
            summary.recommendations.append(
                StrategicRecommendation(
                    title="Tailor Cohort Product Offerings",
                    description="Differentiate product discount packages across validated customer segments.",
                    priority="Medium",
                    estimated_roi=roi,
                    business_impact="Improves customer conversion rates on lower performing segments.",
                    implementation_effort="Medium",
                    timeline="4 weeks",
                    owner="Product Director",
                    confidence=confidence,
                    evidence=evidence,
                )
            )

    # 2. Generate Risk Assessments from root causes (anomalies)
    for rc in root_causes:
        title = rc.get("title", "")
        evidence = rc.get("evidence", "")
        confidence = rc.get("confidence", 0.8)

        if "outlier" in title.lower():
            summary.risks.append(
                RiskAssessment(
                    title="Decision Model Metric Corruption Risk",
                    description="Unremediated outlier values skew average calculations and lead to erroneous business forecasts.",
                    priority="Medium",
                    confidence=confidence,
                    evidence=evidence,
                )
            )
        elif "spike" in title.lower() or "drop" in title.lower():
            summary.risks.append(
                RiskAssessment(
                    title="Platform Ingestion Sync Failures",
                    description="Sudden sequential data jumps indicate transient payload failures or system telemetry lag.",
                    priority="High",
                    confidence=confidence,
                    evidence=evidence,
                )
            )
        else:
            summary.risks.append(
                RiskAssessment(
                    title="Data Quality Degradation Risk",
                    description="General pattern variance signals ingestion parser mismatches.",
                    priority="Low",
                    confidence=confidence,
                    evidence=evidence,
                )
            )

    # 3. Rank Recommendations by ROI descending, then by confidence descending
    summary.recommendations.sort(key=lambda x: (x.estimated_roi, x.confidence), reverse=True)

    # Deduplicate all strategy lists
    summary.opportunities = deduplicate_by_title(summary.opportunities)
    summary.recommendations = deduplicate_by_title(summary.recommendations)
    summary.risks = deduplicate_by_title(summary.risks)
    summary.warnings = list(dict.fromkeys(summary.warnings))

    return summary

"""
Insight Forge V2 — Business Reasoning Engine.

Implements the 5 Whys traceback builder, competing hypothesis generator, and
evidence-based validation ranking/rejection filters in pure Python.
"""

from typing import Any
from app.ai.schemas.business import RootCause, BusinessHypothesis, BusinessAnalysisSummary
from app.ai.utils.helpers import deduplicate_by_title


def perform_5_whys(anomaly: dict[str, Any]) -> RootCause:

    """Build a structured 5 Whys root cause chain backtracing data anomalies."""
    title = anomaly.get("title", "Unknown Anomaly")
    affected = anomaly.get("affected_columns", [])
    col_str = affected[0] if affected else "unknown_column"

    why_steps = []
    if "outlier" in title.lower():
        why_steps = [
            f"1. Why: Extreme metric value entry detected in column '{col_str}'.",
            "2. Why: Isolated data entry error, pipeline mis-mapping, or extreme transaction surge.",
            "3. Why: Concurrent ingestion payload execution without database validation rules.",
            "4. Why: Inadequate boundary validation constraints in ingestion schema.",
            "5. Why: Lack of strict application threshold check rules on incoming API payloads."
        ]
        impact = f"Compromises statistical integrity of '{col_str}' averages and modeling calculations."
    elif "spike" in title.lower() or "drop" in title.lower():
        direction = "spike" if "spike" in title.lower() else "drop"
        why_steps = [
            f"1. Why: Sudden sequential step-change {direction} observed in '{col_str}'.",
            "2. Why: Severe localized shift in transaction volumes or batch job failures.",
            "3. Why: Scheduled maintenance window, service outage, or promotional event launch.",
            "4. Why: Marketing or infrastructure change executed without rate limit bounds.",
            "5. Why: Lack of synchronized deployment calendars between DevOps and business campaigns."
        ]
        impact = "Triggers false trend shifts and misleads automated growth projections."
    else:
        why_steps = [
            f"1. Why: Unexpected pattern deviation identified in column '{col_str}'.",
            "2. Why: Localized record mismatch during ETL parsing.",
            "3. Why: Incomplete cleaning rules applied to raw source imports.",
            "4. Why: Data schema discrepancies between third-party exports.",
            "5. Why: Absence of real-time schema registry validation rules on file ingestion."
        ]
        impact = "Increases column noise and reduces downstream classification confidence."

    return RootCause(
        title=f"Root Cause of {title}",
        description="\n".join(why_steps),
        evidence=anomaly.get("evidence", ""),
        confidence=anomaly.get("confidence", 0.8),
        business_impact=impact,
        supporting_findings=[title],
    )


def generate_competing_hypotheses(
    insight: dict[str, Any],
    anomalies: list[dict[str, Any]],
) -> list[BusinessHypothesis]:
    """Formulate competing business hypotheses for a given validated insight."""
    title = insight.get("title", "Generic Insight")
    affected = insight.get("affected_columns", [])
    col_str = affected[0] if affected else "unknown_column"
    col2_str = affected[1] if len(affected) > 1 else ""

    hypotheses = []
    # Check if there is an anomaly in the target columns
    has_anomaly = any(col in a.get("affected_columns", []) for col in affected for a in anomalies)

    if "regression" in title.lower() or "growth" in title.lower():
        # Hypothesis 1: Organic Growth (Business Case)
        hyp_organic = BusinessHypothesis(
            title=f"Organic Market Growth in {col_str}",
            description=f"The slope changes in {col_str} represent genuine increases in customer acquisition, organic demand, or market expansion.",
            evidence=f"Validated trend confidence: {insight.get('confidence', 0.9):.2%}.",
            confidence=0.85 if not has_anomaly else 0.40,
            business_impact="Enables inventory expansion and positive revenue forecasts.",
            supporting_findings=[title],
            status="Pending",
        )
        # Hypothesis 2: Data Duplication / Inflation Case (Technical Case)
        hyp_technical = BusinessHypothesis(
            title=f"Ingestion Double-Logging in {col_str}",
            description=f"The statistical growth trend in {col_str} is an artifact of duplicate transaction payloads or double-logging in database systems.",
            evidence="Pending verification of sequence anomalies.",
            confidence=0.20 if not has_anomaly else 0.80,
            business_impact="False metrics lead to over-budgeting and artificial revenue projections.",
            supporting_findings=[title],
            status="Pending",
        )
        hypotheses.extend([hyp_organic, hyp_technical])

    elif "group variance" in title.lower() or "anova" in title.lower():
        # Hypothesis 1: Segment Differentiation
        hyp_segment = BusinessHypothesis(
            title=f"Genuine Cohort Differentiation by {col_str}",
            description=f"The differences in '{col2_str}' means across categories in '{col_str}' are driven by fundamental behavioral cohort variance.",
            evidence=f"ANOVA group variance confidence: {insight.get('confidence', 0.9):.2%}.",
            confidence=0.80 if not has_anomaly else 0.30,
            business_impact="Validates cohort target segmentation and customized pricing strategies.",
            supporting_findings=[title],
            status="Pending",
        )
        # Hypothesis 2: Confounding Operational Factor
        hyp_confounding = BusinessHypothesis(
            title=f"Operational Confounding in {col2_str}",
            description=f"The cohort differences are not causal, but driven by a confounding temporal/regional factor not captured in '{col_str}'.",
            evidence="Pending verification of data distribution noise.",
            confidence=0.30 if not has_anomaly else 0.75,
            business_impact="Interventions on group labels will yield no real ROI due to wrong root causes.",
            supporting_findings=[title],
            status="Pending",
        )
        hypotheses.extend([hyp_segment, hyp_confounding])

    else:
        # Fallback General Hypotheses
        hyp_a = BusinessHypothesis(
            title=f"Organic Behavior Drive for {title}",
            description="The finding represents authentic behavioral dynamics.",
            evidence=f"Confidence: {insight.get('confidence', 0.8):.2%}.",
            confidence=0.70,
            business_impact="Provides opportunities for growth focus.",
            supporting_findings=[title],
            status="Pending",
        )
        hyp_b = BusinessHypothesis(
            title=f"Measurement Bias for {title}",
            description="The finding represents systematic tracking or measurement bias.",
            evidence="No clear validation.",
            confidence=0.30,
            business_impact="Actions taken on this metric will not transfer to general outcomes.",
            supporting_findings=[title],
            status="Pending",
        )
        hypotheses.extend([hyp_a, hyp_b])

    return hypotheses


def evaluate_and_rank_hypotheses(
    hypotheses: list[BusinessHypothesis],
    anomalies: list[dict[str, Any]],
) -> dict[str, list[BusinessHypothesis]]:
    """Validate, rank, and reject competing hypotheses based on evidence weights and anomalies.

    Rule-based validation:
    - If a technical hypothesis (duplicate entries/error) aligns with a detected anomaly, validate it.
    - If a business growth hypothesis aligns with columns containing anomalies, reject it.
    - If no anomalies are present, validate organic growth and reject duplication hypotheses.
    """
    validated = []
    rejected = []

    # Map anomalies by affected columns
    anomaly_cols = set()
    for a in anomalies:
        for col in a.get("affected_columns", []):
            anomaly_cols.add(col)

    for h in hypotheses:
        # Use helper check based on title
        is_technical = "ingestion" in h.title.lower() or "double-logging" in h.title.lower() or "confounding" in h.title.lower() or "bias" in h.title.lower()

        # If target columns or title mentions columns that contain anomalies
        has_anomaly_overlap = False
        for col in anomaly_cols:
            if col in h.title or any(col in f for f in h.supporting_findings):
                has_anomaly_overlap = True

        if is_technical:
            if has_anomaly_overlap:
                h.status = "Validated"
                h.confidence = 0.90
                h.evidence = "Validated: Quality anomalies/outliers detected in target columns."
                validated.append(h)
            else:
                h.status = "Rejected"
                h.confidence = 0.10
                h.evidence = "Rejected: Ingestion flow is stable; no quality anomalies detected."
                rejected.append(h)
        else:  # Business / Organic Growth case
            if has_anomaly_overlap:
                h.status = "Rejected"
                h.confidence = 0.15
                h.evidence = "Rejected: Data quality anomalies detected in target columns. Growth slope may be artificially skewed."
                rejected.append(h)
            else:
                h.status = "Validated"
                h.confidence = 0.95
                h.evidence = "Validated: Clear trend without any conflicting quality warnings."
                validated.append(h)

    # Sort validated hypotheses by confidence descending
    validated.sort(key=lambda x: x.confidence, reverse=True)

    return {"validated": validated, "rejected": rejected}


def run_business_reasoning(
    anomalies: list[dict[str, Any]],
    insights: list[dict[str, Any]],
    validated_findings: list[dict[str, Any]],
) -> BusinessAnalysisSummary:
    """Execute AIBusinessAnalyst reasoning flow."""
    summary = BusinessAnalysisSummary()

    # 1. Generate 5 Whys Root Causes for anomalies
    for a in anomalies:
        summary.root_causes.append(perform_5_whys(a))

    # 2. Generate competing hypotheses for insights
    all_hypotheses = []
    for i in insights:
        all_hypotheses.extend(generate_competing_hypotheses(i, anomalies))

    # 3. Evaluate and rank hypotheses
    evaluation = evaluate_and_rank_hypotheses(all_hypotheses, anomalies)
    summary.validated_hypotheses = deduplicate_by_title(evaluation["validated"])
    summary.rejected_hypotheses = deduplicate_by_title(evaluation["rejected"])
    summary.generated_hypotheses = deduplicate_by_title(all_hypotheses)
    summary.root_causes = deduplicate_by_title(summary.root_causes)

    # 4. Compile business reasoning commentary
    commentary = []
    if summary.root_causes:
        commentary.append(f"Identified {len(summary.root_causes)} operational root cause chains.")
    for h in summary.validated_hypotheses:
        commentary.append(f"Validated hypothesis: '{h.title}' (Conf: {h.confidence:.2%}) due to: {h.evidence}")
    for hr in summary.rejected_hypotheses:
        commentary.append(f"Challenged and rejected: '{hr.title}' due to: {hr.evidence}")

    if not commentary:
        commentary = ["Operational profiles and metrics appear standard and within bounds."]
    summary.business_reasoning = commentary

    return summary

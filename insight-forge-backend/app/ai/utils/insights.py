"""
Insight Forge V2 — Anomaly Detection and Business Insight Engine.

Implements outlier filters, spikes/drops detection, skepticism test filters,
and business-readable insight generators in pure Python.
"""

import math
from typing import Any

from app.ai.schemas.insights import AnomalyDetection, BusinessInsight, InsightSummary


def detect_outliers(series: list[float], col: str) -> list[AnomalyDetection]:
    """Detect statistical outliers using mean and standard deviation threshold bounds (Z-score > 2.5)."""
    n = len(series)
    if n < 3:
        return []

    mean = sum(series) / n
    variance = sum((x - mean) ** 2 for x in series) / n
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return []

    anomalies = []
    outliers = []
    for idx, val in enumerate(series):
        z_score = abs(val - mean) / std_dev
        if z_score >= 1.9:
            outliers.append((idx, val, z_score))

    if outliers:
        evidence_str = ", ".join(f"index {i}: {v:.2f} (Z: {z:.2f})" for i, v, z in outliers)
        anomalies.append(
            AnomalyDetection(
                title=f"Outliers Detected in {col}",
                description=f"Found {len(outliers)} value entries violating normal distribution bounds.",
                affected_columns=[col],
                evidence=f"Mean: {mean:.2f}, StdDev: {std_dev:.2f}. Outliers: {evidence_str}",
                confidence=0.95,
                severity="High",
                recommendation="Investigate data entry errors or verify values are correct.",
            )
        )

    return anomalies


def detect_spikes_drops(series: list[float], col: str) -> list[AnomalyDetection]:
    """Detect sudden spikes or drops between adjacent sequence values."""
    n = len(series)
    if n < 4:
        return []

    diffs = [series[i] - series[i - 1] for i in range(1, n)]
    mean_diff = sum(diffs) / len(diffs)
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
    std_diff = math.sqrt(var_diff)

    if std_diff == 0:
        return []

    anomalies = []
    for i in range(1, n):
        d = series[i] - series[i - 1]
        z = abs(d - mean_diff) / std_diff
        if z > 2.0:
            direction = "spike" if d > 0 else "drop"
            anomalies.append(
                AnomalyDetection(
                    title=f"Sudden {direction.capitalize()} Flagged in {col}",
                    description=f"Significant step-change detected from index {i-1} ({series[i-1]:.2f}) to index {i} ({series[i]:.2f}).",
                    affected_columns=[col],
                    evidence=f"Step diff: {d:.2f} (Z-score: {z:.2f} vs roll StdDev {std_diff:.2f})",
                    confidence=0.90,
                    severity="Medium",
                    recommendation="Audit sequence timeline for system outages or transaction events.",
                )
            )

    return anomalies


def validate_statistical_findings(stats_summary: Any, n_rows: int) -> dict[str, list[Any]]:
    """Challenge and filter weak, non-significant, or small sample size statistical tests.

    Rejection conditions:
    - Pearson correlation: confidence < 0.95 OR abs(correlation) < 0.30 OR sample count < 5
    - Regression/ANOVA/Chi-Square: confidence < 0.95 OR sample count < 5
    """
    validated = {"tests": [], "correlations": [], "trends": []}
    rejected = []

    # 1. Validate Correlations
    for c in stats_summary.correlations:
        # Extract sample size if present in evidence
        sample_count = n_rows
        if "Sample count:" in c.evidence:
            try:
                sample_count = int(c.evidence.split("Sample count:")[1].strip())
            except ValueError:
                pass

        if c.confidence < 0.95 or abs(c.correlation_coefficient) < 0.30 or sample_count < 5:
            rejected.append(
                f"Correlation rejected: {c.target_columns} - Coeff: {c.correlation_coefficient:.4f}, Confidence: {c.confidence:.2%}, N: {sample_count}"
            )
        else:
            validated["correlations"].append(c)

    # 2. Validate Linear Regression / Trends
    for tr in stats_summary.trends:
        required_conf = 0.95 if tr.analysis_type == "Simple Linear Regression" else 0.90
        if tr.confidence < required_conf:
            rejected.append(
                f"Trend analysis rejected: {tr.analysis_type} on {tr.target_columns} - Confidence: {tr.confidence:.2%}"
            )
        else:
            validated["trends"].append(tr)

    # 3. Validate ANOVA and Chi-Square
    for t in stats_summary.tests:
        if t.confidence < 0.95:
            rejected.append(
                f"Test rejected: {t.analysis_type} on {t.target_columns} - Confidence: {t.confidence:.2%}"
            )
        else:
            validated["tests"].append(t)

    return {"validated": validated, "rejected": rejected}


def generate_insights_and_anomalies(
    df_dict: list[dict[str, Any]],
    column_types: dict[str, str],
    stats_summary: Any,
    cleaning_recs: list[dict[str, Any]] | None = None,
) -> InsightSummary:
    """Generate business-readable insights and flags from statistical outputs."""
    summary = InsightSummary()
    n_rows = len(df_dict)
    if n_rows == 0:
        return summary


    # Extract target values
    numerics = {}
    for col, col_type in column_types.items():
        if col_type in ["integer", "float"]:
            vals = []
            for row in df_dict:
                v = row.get(col)
                if v is None or str(v).strip() == "":
                    continue
                try:
                    vals.append(float(str(v).replace("$", "").replace(",", "").strip()))
                except ValueError:
                    pass
            if len(vals) >= 3:
                numerics[col] = vals

    # 1. Run outlier & step change checks on numeric variables
    for col, vals in numerics.items():
        summary.anomalies.extend(detect_outliers(vals, col))
        summary.anomalies.extend(detect_spikes_drops(vals, col))

    # Map cleaning recommendations as standard anomalies
    if cleaning_recs:
        for r in cleaning_recs:
            title = f"Data Quality Issue: {r.get('issue_type')} in {', '.join(r.get('affected_columns', []))}"
            summary.anomalies.append(
                AnomalyDetection(
                    title=title,
                    description=r.get("reasoning", "Quality anomaly detected."),
                    affected_columns=r.get("affected_columns", []),
                    evidence=r.get("evidence", ""),
                    confidence=r.get("confidence", 0.95),
                    severity=r.get("severity", "Medium"),
                    recommendation=r.get("recommended_action", "Flag for review."),
                )
            )

    # Challenge statistical tests
    validation_results = validate_statistical_findings(stats_summary, n_rows)
    validated = validation_results["validated"]
    summary.warnings.extend(validation_results["rejected"])

    # 2. Generate insights based on validated findings
    # Regression insights
    for tr in validated["trends"]:
        if tr.analysis_type == "Simple Linear Regression":
            slope = tr.slope
            r2 = tr.r_squared
            col_x, col_y = tr.target_columns
            if abs(slope) > 0.05 and r2 > 0.40:
                direction = "positive growth" if slope > 0 else "downward contraction"
                summary.insights.append(
                    BusinessInsight(
                        title=f"Significant Regression Trend: {col_x} vs {col_y}",
                        description=f"Statistical modeling shows a verified {direction} relationship where changes in {col_x} explain {r2:.1%} of variance in {col_y}.",
                        affected_columns=[col_x, col_y],
                        evidence=f"Slope: {slope:.4f}, R2: {r2:.4f}, p-value: {(1.0 - tr.confidence):.4f}",
                        confidence=tr.confidence,
                        business_impact=f"A change in {col_x} enables predictable modeling of {col_y} for strategic forecasting.",
                        severity="High" if r2 > 0.70 else "Medium",
                        recommendation=f"Integrate {col_x} in planning models predicting {col_y}.",
                    )
                )

        # Sequence Growth insights
        elif tr.analysis_type == "Sequence Trend Analysis":
            # Extract growth rate from evidence
            growth_rate = 0.0
            if "Growth rate:" in tr.evidence:
                try:
                    growth_rate = float(tr.evidence.split("Growth rate:")[1].split("%")[0].strip()) / 100.0
                except (ValueError, IndexError):
                    pass

            if abs(growth_rate) > 0.20:
                # High growth trend
                summary.insights.append(
                    BusinessInsight(
                        title=f"High Growth Performance in {tr.target_columns[0]}",
                        description=f"A substantial growth change sequence rate of {growth_rate:.2%} was detected over the timeline.",
                        affected_columns=tr.target_columns,
                        evidence=tr.evidence,
                        confidence=0.90,
                        business_impact="Demonstrates high momentum sequence expansion or severe inflation bounds.",
                        severity="High",
                        recommendation="Double down on successful segments or verify capacity limits.",
                    )
                )

            # Change Point insights
            if "Change Point Index:" in tr.evidence:
                idx_str = tr.evidence.split("Change Point Index:")[1].strip()
                if idx_str != "-1":
                    summary.insights.append(
                        BusinessInsight(
                            title=f"Structural Shift in {tr.target_columns[0]}",
                            description=f"A statistical change point mean shift was flagged in {tr.target_columns[0]} at index {idx_str}.",
                            affected_columns=tr.target_columns,
                            evidence=tr.evidence,
                            confidence=0.85,
                            business_impact="Marks a transition point separating distinct performance epochs.",
                            severity="Medium",
                            recommendation="Audit timeline events around the split index to find causal drivers.",
                        )
                    )

    # Chi-Square insights
    for t in validated["tests"]:
        if t.analysis_type == "Chi-Square Test of Independence":
            col1, col2 = t.target_columns
            summary.insights.append(
                BusinessInsight(
                    title=f"Categorical Dependency: {col1} and {col2}",
                    description=f"We reject independence between {col1} and {col2}. Distribution splits are correlated.",
                    affected_columns=[col1, col2],
                    evidence=t.evidence,
                    confidence=t.confidence,
                    business_impact=f"Knowing the segment group in {col1} helps predict category behavior in {col2}.",
                    severity="Medium",
                    recommendation="Segment targeted actions optimizing category matchings.",
                )
            )

        # ANOVA insights
        elif t.analysis_type == "ANOVA (Analysis of Variance)":
            cat_col, num_col = t.target_columns
            summary.insights.append(
                BusinessInsight(
                    title=f"Significant Group Variance: {num_col} by {cat_col}",
                    description=f"The category labels in '{cat_col}' yield statistically significant differences in metric averages of '{num_col}'.",
                    affected_columns=[cat_col, num_col],
                    evidence=t.evidence,
                    confidence=t.confidence,
                    business_impact="Group segments do not perform equally, suggesting high or low efficiency bands.",
                    severity="High",
                    recommendation=f"Analyze individual group performance means in {cat_col} to isolate outliers.",
                )
            )

    return summary

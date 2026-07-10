"""
Insight Forge V2 — Data Cleaning Logic and Certification.

Detects casing, whitespace, numeric bounds, dates, duplicates, and patterns, returning summaries and logs.
"""

import re
from typing import Any

from app.ai.schemas.cleaning import CleaningLogEntry, CleaningRecommendation, TrustedDatasetSummary
from app.ai.utils.profiler import profile_dataset


def map_certification(
    quality_score: float, total_issues: int, critical_issues: int
) -> str:
    """Map quality score and critical issues count to certification tier.

    Tier rules:
    - Certified: score >= 0.95 and critical == 0 and total == 0
    - Certified with Warnings: score >= 0.85 and critical == 0 and total > 0
    - Requires Review: score >= 0.60 or critical > 0
    - Not Certified: score < 0.60 or critical > 3
    """
    if quality_score < 0.60 or critical_issues > 3:
        return "Not Certified"
    if critical_issues > 0 or quality_score < 0.85:
        return "Requires Review"
    if total_issues > 0:
        return "Certified with Warnings"
    return "Certified"


def detect_cleaning_recommendations(
    df_dict: list[dict[str, Any]], columns: list[str], dataset_name: str
) -> list[CleaningRecommendation]:
    """Inspect dataset elements to compile remediation recommendations for quality issues."""
    recommendations = []
    total_rows = len(df_dict)
    if total_rows == 0:
        return []

    # Map column lists
    col_values: dict[str, list[Any]] = {col: [] for col in columns}
    for row in df_dict:
        for col in columns:
            col_values[col].append(row.get(col))

    # 1. Duplicate rows check
    serialized_rows = [str(sorted(row.items())) for row in df_dict]
    unique_rows = set(serialized_rows)
    duplicate_rows_count = total_rows - len(unique_rows)
    if duplicate_rows_count > 0:
        recommendations.append(
            CleaningRecommendation(
                issue_type="DUPLICATE_ROWS",
                affected_columns=columns,
                severity="Medium",
                recommended_action="Remove duplicates",
                reasoning=f"Found {duplicate_rows_count} duplicate row copies in the dataset.",
                confidence=0.98,
                evidence=f"Unique rows: {len(unique_rows)} / {total_rows}",
            )
        )

    # Compile profiles for type and null metadata
    profile = profile_dataset(df_dict, columns, dataset_name)

    # 2. Iterate columns to check specific items
    for col in columns:
        vals = col_values[col]
        non_nulls = [v for v in vals if v is not None and str(v).strip() != ""]
        non_null_count = len(non_nulls)
        col_profile = profile.column_profiles[col]

        # A. Missing values check
        if col_profile.null_count > 0:
            severity = "High" if col_profile.business_importance_score >= 0.8 else "Medium"
            recommendations.append(
                CleaningRecommendation(
                    issue_type="MISSING_VALUES",
                    affected_columns=[col],
                    severity=severity,
                    recommended_action="Impute value (recommendation only)",
                    reasoning=f"Column '{col}' contains {col_profile.null_count} missing records.",
                    confidence=0.95,
                    evidence=f"Null percentage: {col_profile.null_percentage:.1%}",
                )
            )

        # B. Duplicate Identifiers
        col_lower = col.lower()
        is_id = "id" in col_lower or "key" in col_lower
        if is_id and col_profile.duplicate_percentage > 0:
            recommendations.append(
                CleaningRecommendation(
                    issue_type="DUPLICATE_IDENTIFIERS",
                    affected_columns=[col],
                    severity="Critical",
                    recommended_action="Flag for manual review",
                    reasoning=f"Identifier column '{col}' contains duplicates which violates uniqueness.",
                    confidence=1.0,
                    evidence=f"Duplicate percentage: {col_profile.duplicate_percentage:.1%}",
                )
            )

        # String-specific checks
        if col_profile.data_type == "string" and non_null_count > 0:
            # C. Whitespace and empty strings checks
            whitespaces = sum(1 for v in non_nulls if str(v).strip() != str(v))
            empty_strings = sum(1 for v in vals if v is not None and str(v).strip() == "")

            if whitespaces > 0:
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="WHITESPACE_ISSUES",
                        affected_columns=[col],
                        severity="Low",
                        recommended_action="Standardize formatting",
                        reasoning=f"Column '{col}' has {whitespaces} values with leading/trailing whitespaces.",
                        confidence=0.99,
                        evidence=f"Affected counts: {whitespaces} / {non_null_count} records",
                    )
                )

            if empty_strings > 0:
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="EMPTY_STRINGS",
                        affected_columns=[col],
                        severity="Low",
                        recommended_action="Impute value (recommendation only)",
                        reasoning=f"Column '{col}' contains {empty_strings} blank strings.",
                        confidence=0.95,
                        evidence=f"Empty strings: {empty_strings}",
                    )
                )

            # D. Casing inconsistency
            caps = 0
            lowers = 0
            titles = 0
            for v in non_nulls:
                v_str = str(v).strip()
                if any(char.isalpha() for char in v_str):
                    if v_str.isupper():
                        caps += 1
                    elif v_str.islower():
                        lowers += 1
                    elif v_str.istitle():
                        titles += 1

            # If casing is mixed
            casing_types = sum(1 for c in [caps, lowers, titles] if c > 0)
            if casing_types > 1:
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="CASING_INCONSISTENCY",
                        affected_columns=[col],
                        severity="Low",
                        recommended_action="Normalize categories",
                        reasoning=f"Column '{col}' has mixed casings (Upper: {caps}, Lower: {lowers}, Title: {titles}).",
                        confidence=0.90,
                        evidence=f"Casing types counts: {casing_types}",
                    )
                )

            # E. Inconsistent categorical values (e.g. active vs Active)
            lowercased = [str(v).strip().lower() for v in non_nulls]
            if len(set(lowercased)) < len(set(non_nulls)):
                # There are strings that are distinct but identical when lowercased
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="INCONSISTENT_CATEGORICAL_VALUES",
                        affected_columns=[col],
                        severity="Low",
                        recommended_action="Normalize categories",
                        reasoning=f"Column '{col}' contains categories differing only by case/spacing variations.",
                        confidence=0.95,
                        evidence=f"Distinct raw: {len(set(non_nulls))}, Distinct lower: {len(set(lowercased))}",
                    )
                )

        # F. Invalid email / phone format
        if non_null_count > 0:
            email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
            phone_regex = r"^\+?[\d\s\-]{7,15}$"

            emails = sum(1 for v in non_nulls if re.match(email_regex, str(v).strip()))
            phones = sum(1 for v in non_nulls if re.match(phone_regex, str(v).strip()))

            if 0 < emails < non_null_count and ("email" in col_lower or emails / non_null_count > 0.5):
                failed = non_null_count - emails
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="INVALID_EMAIL_FORMAT",
                        affected_columns=[col],
                        severity="High",
                        recommended_action="Flag for manual review",
                        reasoning=f"Column '{col}' contains {failed} values violating email formatting standard rules.",
                        confidence=0.98,
                        evidence=f"Failing matches: {failed} / {non_null_count}",
                    )
                )

            is_date_col = "date" in col_lower or "time" in col_lower or "timestamp" in col_lower or col_profile.data_type == "date"
            if not is_date_col and 0 < phones < non_null_count and ("phone" in col_lower or phones / non_null_count > 0.5):
                failed = non_null_count - phones
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="INVALID_PHONE_NUMBER",
                        affected_columns=[col],
                        severity="Medium",
                        recommended_action="Flag for manual review",
                        reasoning=f"Column '{col}' contains {failed} values violating phone numbering rules.",
                        confidence=0.92,
                        evidence=f"Failing matches: {failed} / {non_null_count}",
                    )
                )

        # G. Out-of-range checks
        if col_profile.data_type in ["integer", "float"] and non_null_count > 0:
            # Filter castable numerics
            numerics = []
            for v in non_nulls:
                try:
                    numerics.append(float(str(v).replace("$", "").replace(",", "").strip()))
                except ValueError:
                    pass

            if numerics:
                # Custom thresholds: e.g. check for negative values in quantity/price/amount
                has_negatives = any(n < 0 for n in numerics)
                if has_negatives and any(k in col_lower for k in ["qty", "quantity", "amt", "amount", "price", "val"]):
                    neg_count = sum(1 for n in numerics if n < 0)
                    recommendations.append(
                        CleaningRecommendation(
                            issue_type="OUT_OF_RANGE_VALUES",
                            affected_columns=[col],
                            severity="High",
                            recommended_action="Flag for manual review",
                            reasoning=f"Numeric column '{col}' contains negative values.",
                            confidence=0.99,
                            evidence=f"Negative counts: {neg_count} records",
                        )
                    )

        # H. Mixed Formatting check (e.g. dates matching both YYYY-MM-DD and MM/DD/YYYY)
        if col_profile.data_type == "date" and non_null_count > 0:
            dash_pattern = r"^\d{4}-\d{2}-\d{2}$"
            slash_pattern = r"^\d{2}/\d{2}/\d{4}$"

            dashes = sum(1 for v in non_nulls if re.match(dash_pattern, str(v).strip()))
            slashes = sum(1 for v in non_nulls if re.match(slash_pattern, str(v).strip()))

            if dashes > 0 and slashes > 0:
                recommendations.append(
                    CleaningRecommendation(
                        issue_type="MIXED_FORMATTING",
                        affected_columns=[col],
                        severity="Medium",
                        recommended_action="Standardize formatting",
                        reasoning=f"Column '{col}' has mixed date format styling.",
                        confidence=0.95,
                        evidence=f"YYYY-MM-DD: {dashes}, MM/DD/YYYY: {slashes}",
                    )
                )

    return recommendations


def calculate_dataset_quality_score(
    base_score: float, recommendations: list[CleaningRecommendation]
) -> float:
    """Centralized quality score computation deducting points based on issue severity."""
    score = base_score
    for r in recommendations:
        sev = r.severity.lower()
        if sev == "critical":
            score -= 0.1
        elif sev == "high":
            score -= 0.05
        elif sev == "medium":
            score -= 0.02
        else:
            score -= 0.01
    return max(0.0, min(1.0, score))


def generate_trusted_dataset(
    df_dict: list[dict[str, Any]], columns: list[str], dataset_name: str
) -> tuple[TrustedDatasetSummary, list[CleaningLogEntry]]:
    """Inspect dataset, extract clean recommendations, certify the dataset, and build audit logs."""
    row_count = len(df_dict)
    warnings = []

    if row_count == 0:
        warnings.append("Dataset is empty. Processing canceled.")
        summary = TrustedDatasetSummary(
            overall_quality_score=0.0,
            total_issues_detected=0,
            critical_issues_count=0,
            warnings=warnings,
            cleaning_recommendations=[],
            certification_status="Not Certified",
        )
        return summary, []

    # Map column lists
    col_values: dict[str, list[Any]] = {col: [] for col in columns}
    for row in df_dict:
        for col in columns:
            col_values[col].append(row.get(col))

    # 1. Profile quality metrics
    profile = profile_dataset(df_dict, columns, dataset_name)
    warnings.extend(profile.warnings)

    # 2. Detect issues & recommendations
    recommendations = detect_cleaning_recommendations(df_dict, columns, dataset_name)

    # 3. Analyze severity categories
    critical_issues = sum(1 for r in recommendations if r.severity.lower() == "critical")
    total_issues = len(recommendations)

    # Deduct overall quality based on recommendations (centralized calculation)
    quality_score = calculate_dataset_quality_score(profile.overall_quality_score, recommendations)

    quality_score = max(0.0, min(1.0, quality_score))

    # 4. Certification level mapping
    cert_status = map_certification(quality_score, total_issues, critical_issues)

    summary = TrustedDatasetSummary(
        overall_quality_score=quality_score,
        total_issues_detected=total_issues,
        critical_issues_count=critical_issues,
        warnings=warnings,
        cleaning_recommendations=recommendations,
        certification_status=cert_status,
    )

    # 5. Build structured CleaningLogEntries
    cleaning_log = []
    for r in recommendations:
        cleaning_log.append(
            CleaningLogEntry(
                issue=f"{r.issue_type} in columns: {', '.join(r.affected_columns)}",
                recommendation=r.recommended_action,
                confidence=r.confidence,
                evidence=r.evidence,
                status="PROPOSED",
            )
        )

    return summary, cleaning_log

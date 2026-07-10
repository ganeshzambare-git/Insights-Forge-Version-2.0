"""
Insight Forge V2 — Profiler Mathematics and Constraint Utilities.

Implements pure Python functions for shannon entropy, statistics, quality scores, and constraints.
"""

import math
import re
from collections import Counter
from typing import Any

from app.ai.schemas.profiler import ColumnProfile, ConstraintAnalysis, DatasetProfile


def calculate_entropy(values: list[Any]) -> float:
    """Compute Shannon Entropy for a list of values.

    H = -sum(P(x) * log2(P(x)))
    """
    if not values:
        return 0.0

    total = len(values)
    # Represent values as strings to handle unhashable dictionary types or mixed variables safely
    stringified = [str(v) if v is not None else "" for v in values]
    counts = Counter(stringified)

    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    return abs(entropy)


def infer_data_type(values: list[Any]) -> tuple[str, float]:
    """Infer the probable business data type of a list of values.

    Returns:
        A tuple of (type_string, confidence_score).
    """
    non_nulls = [v for v in values if v is not None and str(v).strip() != ""]
    if not non_nulls:
        return "Unknown", 0.0

    total = len(non_nulls)
    ints = 0
    floats = 0
    bools = 0
    dates = 0

    date_patterns = [
        r"^\d{4}-\d{2}-\d{2}$",
        r"^\d{2}/\d{2}/\d{4}$",
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*$",
    ]

    for v in non_nulls:
        v_str = str(v).strip()
        # Check Boolean
        if v_str.lower() in ["true", "false", "yes", "no", "1", "0"] and len(v_str) <= 5:
            bools += 1
            continue

        # Check Date
        is_date = False
        for pat in date_patterns:
            if re.match(pat, v_str):
                is_date = True
                break
        if is_date:
            dates += 1
            continue

        # Check Int/Float
        try:
            int(v_str)
            ints += 1
            continue
        except ValueError:
            pass

        try:
            float(v_str)
            floats += 1
            continue
        except ValueError:
            pass

    if ints == total:
        return "integer", 1.0
    if floats == total or (ints + floats) == total:
        # If mixed ints and floats, treat as float
        return "float", 1.0
    if bools == total:
        return "boolean", 1.0
    if dates == total:
        return "date", 0.95

    # Look for majority
    if ints / total >= 0.8:
        return "integer", ints / total
    if floats / total >= 0.8 or (ints + floats) / total >= 0.8:
        return "float", (ints + floats) / total
    if bools / total >= 0.8:
        return "boolean", bools / total
    if dates / total >= 0.8:
        return "date", dates / total

    return "string", 0.9


def calculate_column_profile(values: list[Any], col_name: str) -> ColumnProfile:
    """Perform data profiling calculations on a column list of values."""
    total_count = len(values)
    if total_count == 0:
        return ColumnProfile(
            data_type="Unknown",
            null_count=0,
            null_percentage=0.0,
            distinct_values=[],
            unique_values_count=0,
            duplicate_percentage=0.0,
            value_distribution={},
            cardinality=0,
            entropy=0.0,
            pattern_consistency=1.0,
            type_confidence=0.0,
            business_importance_score=0.1,
            overall_quality_score=1.0,
        )

    # Null extraction
    nulls = [
        v for v in values if v is None or str(v).strip() == "" or str(v).lower() == "nan"
    ]
    null_count = len(nulls)
    null_percentage = null_count / total_count

    # Non-null values
    non_nulls = [v for v in values if v not in nulls]
    non_null_count = len(non_nulls)

    # Cardinality / Unique counts
    distinct = list(set(non_nulls))
    cardinality = len(distinct)
    unique_values_count = cardinality

    # Value distribution
    counts = Counter(non_nulls)
    top_10_distribution = {str(k): int(v) for k, v in counts.most_common(10)}

    # Duplicate percentage
    duplicate_percentage = 0.0
    if non_null_count > 0:
        # duplicate rows divided by non-null records
        duplicate_percentage = (non_null_count - cardinality) / non_null_count

    # Min, Max, Mean, Std Dev for Numeric values
    min_value = None
    max_value = None
    mean = None
    median = None
    std_dev = None

    # Castable numerics
    numerics = []
    for v in non_nulls:
        try:
            numerics.append(float(str(v).replace("$", "").replace(",", "").strip()))
        except (ValueError, TypeError):
            pass

    if numerics:
        min_value = min(numerics)
        max_value = max(numerics)
        mean = sum(numerics) / len(numerics)
        sorted_nums = sorted(numerics)
        mid = len(sorted_nums) // 2
        if len(sorted_nums) % 2 == 0:
            median = (sorted_nums[mid - 1] + sorted_nums[mid]) / 2
        else:
            median = sorted_nums[mid]
        variance = sum((x - mean) ** 2 for x in numerics) / len(numerics)
        std_dev = math.sqrt(variance)

    # String length statistics
    length_min = None
    length_max = None
    length_mean = None
    str_lengths = [len(str(v)) for v in non_nulls]
    if str_lengths:
        length_min = min(str_lengths)
        length_max = max(str_lengths)
        length_mean = sum(str_lengths) / len(str_lengths)

    # Mode
    mode = None
    if counts:
        mode = counts.most_common(1)[0][0]

    # Inferred details
    data_type, type_confidence = infer_data_type(values)
    entropy = calculate_entropy(values)

    # Pattern consistency (check format structure of non-null strings)
    pattern_consistency = 1.0
    if non_null_count > 0:
        # Check standard format patterns e.g. emails, numbers, dates
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        date_regex = r"^\d{4}-\d{2}-\d{2}$"
        phone_regex = r"^\+?[\d\s\-]{7,15}$"

        emails = 0
        dates = 0
        phones = 0

        for v in non_nulls:
            v_str = str(v).strip()
            if re.match(email_regex, v_str):
                emails += 1
            if re.match(date_regex, v_str):
                dates += 1
            if re.match(phone_regex, v_str):
                phones += 1

        max_matches = max(emails, dates, phones)
        if max_matches > 0:
            pattern_consistency = max_matches / non_null_count

    # Business importance heuristics based on name keywords
    business_importance = 0.5
    col_lower = col_name.lower()
    if "id" in col_lower or "key" in col_lower:
        business_importance = 0.9
    elif "amount" in col_lower or "revenue" in col_lower or "amt" in col_lower or "price" in col_lower:
        business_importance = 0.8
    elif "date" in col_lower or "timestamp" in col_lower or "dt" in col_lower:
        business_importance = 0.7

    # Quality score computation
    # Deduct quality on high null rates and type deviations
    quality_score = max(0.0, 1.0 - null_percentage)
    # Deduct if mixed types exist (meaning some values are castable to numeric and some are not, in a non-string column)
    if data_type in ["integer", "float"] and len(numerics) < non_null_count:
        quality_score = max(0.0, quality_score - 0.2)

    return ColumnProfile(
        data_type=data_type,
        null_count=null_count,
        null_percentage=null_percentage,
        distinct_values=distinct[:10],  # cap distinct values list in response
        unique_values_count=unique_values_count,
        duplicate_percentage=duplicate_percentage,
        min_value=min_value if min_value is not None else (min(distinct) if distinct else None),
        max_value=max_value if max_value is not None else (max(distinct) if distinct else None),
        mean=mean,
        median=median,
        mode=mode,
        std_dev=std_dev,
        value_distribution=top_10_distribution,
        cardinality=cardinality,
        entropy=entropy,
        length_min=length_min,
        length_max=length_max,
        length_mean=length_mean,
        pattern_consistency=pattern_consistency,
        type_confidence=type_confidence,
        business_importance_score=business_importance,
        overall_quality_score=quality_score,
    )


def discover_constraints(
    df_dict: list[dict[str, Any]], columns: list[str]
) -> list[ConstraintAnalysis]:
    """Inspect dataset records to discover primary keys, nullable fields, constant columns, etc."""
    constraints = []
    total_rows = len(df_dict)
    if total_rows == 0:
        return []

    # Map columns to their values list
    col_values: dict[str, list[Any]] = {col: [] for col in columns}
    for row in df_dict:
        for col in columns:
            col_values[col].append(row.get(col))

    for col in columns:
        vals = col_values[col]
        non_nulls = [v for v in vals if v is not None and str(v).strip() != ""]
        non_null_count = len(non_nulls)
        distinct = set(non_nulls)
        distinct_count = len(distinct)

        # 1. Nullable Check
        null_count = total_rows - non_null_count
        if null_count > 0:
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="NULLABLE",
                    columns=[col],
                    confidence=1.0,
                    reasoning=f"Column '{col}' contains {null_count} null or empty values.",
                    evidence=f"Null count: {null_count} ({null_count/total_rows:.1%} of rows)",
                )
            )

        # 2. Constant Column Check
        if distinct_count == 1 and null_count == 0:
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="CONSTANT",
                    columns=[col],
                    confidence=1.0,
                    reasoning=f"Column '{col}' contains only one constant value: '{list(distinct)[0]}'.",
                    evidence="Unique values count: 1",
                )
            )
        elif distinct_count == 1 and null_count > 0:
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="NEAR_CONSTANT",
                    columns=[col],
                    confidence=0.9,
                    reasoning=f"Column '{col}' is constant where values are present, but contains nulls.",
                    evidence=f"Present values: {non_null_count}, Unique: 1, Nulls: {null_count}",
                )
            )

        # 3. Unique / Primary Key Candidate Checks
        if distinct_count == total_rows and null_count == 0:
            # Strong primary key candidate
            col_lower = col.lower()
            confidence = 0.95 if ("id" in col_lower or "key" in col_lower) else 0.8
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="PRIMARY_KEY",
                    columns=[col],
                    confidence=confidence,
                    reasoning=(
                        f"Column '{col}' contains 100% unique, non-null values, "
                        "making it a strong Primary Key candidate."
                    ),
                    evidence=f"Row count: {total_rows}, Distinct count: {distinct_count}",
                )
            )
        elif distinct_count == non_null_count and null_count > 0:
            # Unique constraint candidate
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="UNIQUE",
                    columns=[col],
                    confidence=0.85,
                    reasoning=f"Column '{col}' contains unique values, but is nullable.",
                    evidence=f"Non-null rows: {non_null_count}, Distinct count: {distinct_count}",
                )
            )

        # 4. Possible Categorical Check
        if 1 < distinct_count <= max(3, int(total_rows * 0.15)):
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="CATEGORICAL",
                    columns=[col],
                    confidence=0.85,
                    reasoning=f"Column '{col}' contains low-cardinality values, ideal for categorizations.",
                    evidence=f"Distinct count: {distinct_count} in {total_rows} rows",
                )
            )

        # 5. Numeric Range check
        numerics = []
        for v in non_nulls:
            try:
                numerics.append(float(str(v).strip()))
            except ValueError:
                pass
        if numerics and len(numerics) == non_null_count:
            min_val = min(numerics)
            max_val = max(numerics)
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="NUMERIC_RANGE",
                    columns=[col],
                    confidence=1.0,
                    reasoning=f"Column '{col}' is fully numeric and resides inside a defined range.",
                    evidence=f"Range: [{min_val} to {max_val}] over {len(numerics)} records",
                )
            )

        # 6. Pattern consistency (e.g. date formatting or emails)
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        date_regex = r"^\d{4}-\d{2}-\d{2}$"
        emails = sum(1 for v in non_nulls if re.match(email_regex, str(v).strip()))
        dates = sum(1 for v in non_nulls if re.match(date_regex, str(v).strip()))

        if emails == non_null_count and non_null_count > 0:
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="PATTERN",
                    columns=[col],
                    confidence=0.99,
                    reasoning=f"Column '{col}' strictly follows standard email pattern consistency.",
                    evidence=f"Matches: {emails}/{non_null_count} (100.0%)",
                )
            )
        elif dates == non_null_count and non_null_count > 0:
            constraints.append(
                ConstraintAnalysis(
                    constraint_type="DATE_FORMAT",
                    columns=[col],
                    confidence=0.99,
                    reasoning=f"Column '{col}' strictly follows date ISO-8601 format consistency (YYYY-MM-DD).",
                    evidence=f"Matches: {dates}/{non_null_count} (100.0%)",
                )
            )

    return constraints


def profile_dataset(
    df_dict: list[dict[str, Any]], columns: list[str], dataset_name: str
) -> DatasetProfile:
    """Coordinate the calculations to generate a complete DatasetProfile."""
    row_count = len(df_dict)
    warnings = []

    if row_count == 0:
        warnings.append("Dataset is empty. Row count is 0.")
        return DatasetProfile(
            dataset_name=dataset_name,
            row_count=0,
            column_count=len(columns),
            overall_quality_score=1.0,
            column_profiles={col: calculate_column_profile([], col) for col in columns},
            constraints=[],
            warnings=warnings,
        )

    # Map column lists
    col_values: dict[str, list[Any]] = {col: [] for col in columns}
    for row in df_dict:
        for col in columns:
            col_values[col].append(row.get(col))

    # Profile columns
    column_profiles = {}
    total_quality = 0.0
    for col in columns:
        vals = col_values[col]
        col_profile = calculate_column_profile(vals, col)
        column_profiles[col] = col_profile
        total_quality += col_profile.overall_quality_score

        # Check for mixed type warnings
        non_null_count = sum(1 for v in vals if v is not None and str(v).strip() != "")
        numerics_count = 0
        for v in vals:
            if v is not None and str(v).strip() != "":
                try:
                    float(str(v).replace("$", "").replace(",", "").strip())
                    numerics_count += 1
                except ValueError:
                    pass
        if 0 < numerics_count < non_null_count:
            warnings.append(
                f"Mixed data types detected in column '{col}': "
                f"{numerics_count} numeric values out of {non_null_count} total."
            )

    overall_quality = total_quality / len(columns) if columns else 1.0

    # Constraint discovery
    constraints = discover_constraints(df_dict, columns)

    return DatasetProfile(
        dataset_name=dataset_name,
        row_count=row_count,
        column_count=len(columns),
        overall_quality_score=overall_quality,
        column_profiles=column_profiles,
        constraints=constraints,
        warnings=warnings,
    )

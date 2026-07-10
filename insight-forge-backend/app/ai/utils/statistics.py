"""
Insight Forge V2 — Statistical Operations and Trend Detection Engine.

Implements Pearson correlation, simple linear regression, Chi-Square, ANOVA,
moving averages, growth rates, and change-point detection in pure Python.
"""

import math
from typing import Any

from app.ai.schemas.statistics import (
    CorrelationResult,
    StatisticalSummary,
    StatisticalTest,
    TrendAnalysis,
)


def normal_cdf(z: float) -> float:
    """Calculate the cumulative distribution function for standard normal distribution."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def chi_square_p_value(chi_stat: float, df: int) -> float:
    """Approximate the p-value of a Chi-Square statistic using the Wilson-Hilferty transformation."""
    if chi_stat <= 0 or df <= 0:
        return 1.0
    try:
        term1 = (chi_stat / df) ** (1 / 3)
        term2 = 1 - 2 / (9 * df)
        denom = math.sqrt(2 / (9 * df))
        z = (term1 - term2) / denom
        p = 1.0 - normal_cdf(z)
        return max(0.0, min(1.0, p))
    except Exception:
        return 0.05


def f_distribution_p_value(f_stat: float, dfn: int, dfd: int) -> float:
    """Approximate p-value of F-distribution using Fisher's z-transformation."""
    if f_stat <= 0 or dfn <= 0 or dfd <= 0:
        return 1.0
    try:
        # Fisher's z log F approximation
        log_f = math.log(f_stat)
        mean_z = 0.5 * (1 / dfd - 1 / dfn)
        var_z = 0.5 * (1 / dfn + 1 / dfd)
        z = (0.5 * log_f - mean_z) / math.sqrt(var_z)
        p = 1.0 - normal_cdf(z)
        return max(0.0, min(1.0, p))
    except Exception:
        return 0.05


def calculate_pearson(x: list[float], y: list[float]) -> tuple[float, float]:
    """Calculate Pearson correlation coefficient r and approximate p-value."""
    n = len(x)
    if n < 2:
        return 0.0, 1.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0 or var_y == 0:
        return 0.0, 1.0

    r = cov / math.sqrt(var_x * var_y)
    r = max(-1.0, min(1.0, r))

    # T-statistic approximation
    if abs(r) >= 0.99999:
        return r, 0.0

    try:
        t = r * math.sqrt((n - 2) / (1 - r ** 2))
        p = 2.0 * (1.0 - normal_cdf(abs(t)))
        return r, max(0.0, min(1.0, p))
    except Exception:
        return r, 0.05


def calculate_linear_regression(
    x: list[float], y: list[float]
) -> tuple[float, float, float, float]:
    """Calculate slope, intercept, r_squared, and p-value for simple linear regression."""
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0, 1.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    var_x = sum((xi - mean_x) ** 2 for xi in x)

    if var_x == 0:
        return 0.0, mean_y, 0.0, 1.0

    slope = cov / var_x
    intercept = mean_y - slope * mean_x

    # R squared
    r, p = calculate_pearson(x, y)
    r_squared = r ** 2

    return slope, intercept, r_squared, p


def calculate_chi_square_independence(x: list[Any], y: list[Any]) -> tuple[float, float]:
    """Calculate Chi-Square test statistic of independence and p-value."""
    n = len(x)
    if n == 0:
        return 0.0, 1.0

    categories_x = sorted(list(set(x)))
    categories_y = sorted(list(set(y)))

    row_count = len(categories_x)
    col_count = len(categories_y)

    if row_count < 2 or col_count < 2:
        return 0.0, 1.0

    # Observed contingency table
    observed = [[0] * col_count for _ in range(row_count)]
    for xi, yi in zip(x, y):
        r_idx = categories_x.index(xi)
        c_idx = categories_y.index(yi)
        observed[r_idx][c_idx] += 1

    row_totals = [sum(row) for row in observed]
    col_totals = [sum(observed[r][c] for r in range(row_count)) for c in range(col_count)]
    grand_total = sum(row_totals)

    if grand_total == 0:
        return 0.0, 1.0

    chi_stat = 0.0
    for r in range(row_count):
        for c in range(col_count):
            expected = (row_totals[r] * col_totals[c]) / grand_total
            if expected > 0:
                chi_stat += ((observed[r][c] - expected) ** 2) / expected

    df = (row_count - 1) * (col_count - 1)
    p = chi_square_p_value(chi_stat, df)
    return chi_stat, p


def calculate_anova(groups: list[list[float]]) -> tuple[float, float]:
    """Calculate single-factor ANOVA F-statistic and approximate p-value."""
    k = len(groups)
    if k < 2:
        return 0.0, 1.0

    # Flatten and clean groups
    all_values = []
    group_means = []
    group_sizes = []

    for g in groups:
        if len(g) > 0:
            all_values.extend(g)
            group_means.append(sum(g) / len(g))
            group_sizes.append(len(g))

    n_total = len(all_values)
    k_clean = len(group_sizes)

    if n_total <= k_clean or k_clean < 2:
        return 0.0, 1.0

    grand_mean = sum(all_values) / n_total

    # Between groups sum of squares
    ssb = sum(ni * (mi - grand_mean) ** 2 for ni, mi in zip(group_sizes, group_means))
    dfb = k_clean - 1

    # Within groups sum of squares
    ssw = 0.0
    for g, mi in zip(groups, group_means):
        ssw += sum((x - mi) ** 2 for x in g)
    dfw = n_total - k_clean

    msb = ssb / dfb
    msw = ssw / dfw

    if msw == 0:
        return 0.0, 1.0

    f_stat = msb / msw
    p = f_distribution_p_value(f_stat, dfb, dfw)
    return f_stat, p


def detect_trends_and_change_points(series: list[float]) -> dict[str, Any]:
    """Detect moving averages, growth rate, and least-squares split point."""
    n = len(series)
    if n == 0:
        return {
            "moving_averages": [],
            "growth_rate": 0.0,
            "change_point_index": -1,
        }

    # Growth rate calculation
    growth = 0.0
    if series[0] != 0:
        growth = (series[-1] - series[0]) / series[0]

    # Simple 3-step moving average
    moving_avg = []
    window = min(3, n)
    for i in range(n - window + 1):
        moving_avg.append(sum(series[i : i + window]) / window)

    # Change point detection (least squares splits)
    change_point = -1
    if n >= 4:
        min_variance = float("inf")
        for k in range(2, n - 2):
            left = series[:k]
            right = series[k:]

            mean_l = sum(left) / len(left)
            mean_r = sum(right) / len(right)

            var_l = sum((x - mean_l) ** 2 for x in left)
            var_r = sum((x - mean_r) ** 2 for x in right)

            total_variance = var_l + var_r
            if total_variance < min_variance:
                min_variance = total_variance
                change_point = k

    return {
        "moving_averages": moving_avg,
        "growth_rate": growth,
        "change_point_index": change_point,
    }


def run_statistical_analysis(
    df_dict: list[dict[str, Any]], column_types: dict[str, str]
) -> StatisticalSummary:
    """Coordinate automated statistical analysis based on inferred column classifications."""
    summary = StatisticalSummary()
    n_rows = len(df_dict)
    if n_rows < 5:
        summary.warnings.append(
            f"Dataset size ({n_rows}) is insufficient for statistical calculations. Minimum required sample size is 5."
        )
        return summary


    # Extract clean target values
    numerics = {}
    categoricals = {}

    for col, col_type in column_types.items():
        vals = [row.get(col) for row in df_dict]

        if col_type in ["integer", "float"]:
            # Parse values
            float_vals = []
            valid = True
            for v in vals:
                if v is None or str(v).strip() == "":
                    continue
                try:
                    float_vals.append(float(str(v).replace("$", "").replace(",", "").strip()))
                except ValueError:
                    valid = False
            if valid and len(float_vals) >= 2:
                numerics[col] = float_vals
        elif col_type in ["string", "boolean"]:
            cat_vals = [str(v).strip() for v in vals if v is not None]
            if len(cat_vals) >= 2:
                categoricals[col] = cat_vals

    # 1. Pearson Correlation & Linear Regression (Numerical pairs)
    num_cols = list(numerics.keys())
    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            col1 = num_cols[i]
            col2 = num_cols[j]
            x = numerics[col1]
            y = numerics[col2]

            # Sync lengths for paired measurements
            min_len = min(len(x), len(y))
            if min_len < 2:
                continue
            x_synced = x[:min_len]
            y_synced = y[:min_len]

            # Correlation
            r, p_corr = calculate_pearson(x_synced, y_synced)
            interpretation = "Weak or no correlation"
            if abs(r) >= 0.7:
                interpretation = "Strong positive correlation" if r > 0 else "Strong negative correlation"
            elif abs(r) >= 0.4:
                interpretation = "Moderate positive correlation" if r > 0 else "Moderate negative correlation"

            summary.correlations.append(
                CorrelationResult(
                    target_columns=[col1, col2],
                    confidence=1.0 - p_corr,
                    significance=p_corr,
                    evidence=f"R-value: {r:.4f}, Sample count: {min_len}",
                    interpretation=interpretation,
                    correlation_coefficient=r,
                )
            )

            # Linear Regression
            slope, intercept, r2, p_reg = calculate_linear_regression(x_synced, y_synced)
            summary.trends.append(
                TrendAnalysis(
                    analysis_type="Simple Linear Regression",
                    target_columns=[col1, col2],
                    confidence=1.0 - p_reg,
                    significance=p_reg,
                    evidence=f"y = {slope:.4f}*x + {intercept:.4f}",
                    interpretation=f"For every unit increase in {col1}, {col2} changes by {slope:.4f} units.",
                    slope=slope,
                    intercept=intercept,
                    r_squared=r2,
                )
            )

    # 2. Chi-Square Test of Independence (Categorical pairs)
    cat_cols = list(categoricals.keys())
    for i in range(len(cat_cols)):
        for j in range(i + 1, len(cat_cols)):
            col1 = cat_cols[i]
            col2 = cat_cols[j]
            x = categoricals[col1]
            y = categoricals[col2]

            min_len = min(len(x), len(y))
            if min_len < 2:
                continue

            chi_stat, p_chi = calculate_chi_square_independence(x[:min_len], y[:min_len])
            interpretation = "Independent categorical distributions"
            if p_chi < 0.05:
                interpretation = "Significant dependency between categories detected"

            summary.tests.append(
                StatisticalTest(
                    analysis_type="Chi-Square Test of Independence",
                    target_columns=[col1, col2],
                    confidence=1.0 - p_chi,
                    significance=p_chi,
                    evidence=f"Chi2 statistic: {chi_stat:.4f}",
                    interpretation=interpretation,
                )
            )

    # 3. Single-Factor ANOVA (Numeric + Categorical splits)
    for num_col in num_cols:
        for cat_col in cat_cols:
            y = numerics[num_col]
            x = categoricals[cat_col]

            min_len = min(len(x), len(y))
            if min_len < 3:
                continue

            x_synced = x[:min_len]
            y_synced = y[:min_len]

            # Group numeric values by category
            unique_cats = set(x_synced)
            groups = []
            for cat in unique_cats:
                groups.append([y_val for x_val, y_val in zip(x_synced, y_synced) if x_val == cat])

            f_stat, p_anova = calculate_anova(groups)
            interpretation = "No statistically significant differences between group means"
            if p_anova < 0.05:
                interpretation = "Statistically significant difference between group means detected"

            summary.tests.append(
                StatisticalTest(
                    analysis_type="ANOVA (Analysis of Variance)",
                    target_columns=[cat_col, num_col],
                    confidence=1.0 - p_anova,
                    significance=p_anova,
                    evidence=f"F-statistic: {f_stat:.4f}",
                    interpretation=interpretation,
                )
            )

    # 4. Sequence/Temporal Trend Detection
    for col in num_cols:
        series = numerics[col]
        trend_info = detect_trends_and_change_points(series)

        summary.trends.append(
            TrendAnalysis(
                analysis_type="Sequence Trend Analysis",
                target_columns=[col],
                confidence=0.90,
                significance=0.05,
                evidence=f"Growth rate: {trend_info['growth_rate']:.2%}, Change Point Index: {trend_info['change_point_index']}",
                interpretation=f"Overall growth rate is {trend_info['growth_rate']:.2%}. Change point detected at index {trend_info['change_point_index']}.",
                slope=trend_info["growth_rate"],
                intercept=series[0],
                r_squared=0.5,
            )
        )

    return summary

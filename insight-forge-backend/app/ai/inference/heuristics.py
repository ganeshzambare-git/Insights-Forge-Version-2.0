"""
Insight Forge V2 — Deterministic Dataset Inference Heuristics.

Pure-Python, reproducible replacements for the semantic reasoning previously
delegated to an external LLM. Every result here is derived directly from the
uploaded columns and sample rows — same input always yields the same output.

Two public entry points mirror the schemas the pipeline expects:
  - infer_dataset_understanding -> DatasetUnderstandingLLMResponse
  - infer_analyst_framing       -> AnalystLLMResponse
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.ai.agents.data_engineer import (
    ColumnUnderstandingItem,
    DatasetUnderstandingLLMResponse,
)
from app.ai.schemas.analyst import (
    AnalystLLMResponse,
    BusinessQuestion,
    KPIMetadata,
)

# ============================================================
# VALUE-LEVEL TYPE DETECTION
# ============================================================

_TRUE_FALSE = {"true", "false", "yes", "no", "y", "n", "t", "f", "0", "1"}

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)


def _non_null(values: list[Any]) -> list[Any]:
    """Return values that are neither None nor blank strings."""
    return [v for v in values if v is not None and str(v).strip() != ""]


def _to_float(value: Any) -> float | None:
    """Parse a numeric value tolerating currency, percent, and thousands separators."""
    text = str(value).strip().replace(",", "").replace("$", "").replace("%", "")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _is_number(value: Any) -> bool:
    return _to_float(value) is not None


def _is_date(value: Any) -> bool:
    """Detect ISO or common date string formats."""
    text = str(value).strip()
    if len(text) < 6:
        return False
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            continue
    return False


def _fraction(values: list[Any], predicate: Any) -> float:
    """Fraction of values satisfying a predicate (0.0 for an empty list)."""
    if not values:
        return 0.0
    return sum(1 for v in values if predicate(v)) / len(values)


# ============================================================
# NAME-BASED KEYWORD DICTIONARIES
# ============================================================

_INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "Education": [
        "student", "gpa", "grade", "marks", "score", "attendance", "course",
        "subject", "exam", "cohort", "enrollment", "semester", "faculty",
        "teacher", "class", "school", "college", "university", "credit",
        "tuition", "assignment", "instructor", "department",
    ],
    "Retail": [
        "order", "product", "price", "sku", "sale", "revenue", "customer",
        "cart", "inventory", "discount", "quantity", "stock", "purchase",
    ],
    "Healthcare": [
        "patient", "diagnosis", "treatment", "doctor", "hospital",
        "admission", "medication", "clinic", "symptom",
    ],
    "Finance": [
        "account", "transaction", "balance", "loan", "interest", "payment",
        "credit", "debit", "invoice", "budget",
    ],
    "Human Resources": [
        "employee", "salary", "hire", "attrition", "payroll", "manager",
        "designation", "resignation",
    ],
}

_DOMAIN_BY_INDUSTRY: dict[str, tuple[str, str]] = {
    "Education": ("Academic Performance Management", "Student Outcome Tracking"),
    "Retail": ("Sales & Merchandising", "Order Processing"),
    "Healthcare": ("Clinical Operations", "Patient Care Management"),
    "Finance": ("Financial Operations", "Transaction Processing"),
    "Human Resources": ("Workforce Management", "Employee Lifecycle Tracking"),
    "General": ("General Operations", "Record Keeping"),
}

_FINANCIAL_TOKENS = {
    "price", "amount", "amt", "cost", "revenue", "fee", "salary", "income",
    "budget", "paid", "payment", "balance", "tuition", "charge", "total",
}

_GEO_TOKENS = {
    "country", "city", "state", "province", "region", "zip", "postal",
    "lat", "latitude", "long", "longitude", "address", "location",
}

_ID_TOKENS = {"id", "uuid", "guid", "code", "key", "no", "number"}

_TIME_TOKENS = {"date", "time", "year", "timestamp", "month", "day", "dob", "_at", "_on"}

_ABBREVIATIONS: dict[str, str] = {
    "id": "Identifier",
    "dob": "Date of Birth",
    "qty": "Quantity",
    "amt": "Amount",
    "gpa": "Grade Point Average",
    "avg": "Average",
    "pct": "Percentage",
    "perc": "Percentage",
    "dept": "Department",
    "addr": "Address",
    "num": "Number",
    "no": "Number",
    "ts": "Timestamp",
    "dt": "Date",
    "yr": "Year",
    "mo": "Month",
    "attn": "Attendance",
    "std": "Student",
    "reg": "Registration",
}


def humanize_label(column_name: str) -> str:
    """Convert a raw column header into a readable business label.

    Splits snake_case / camelCase, expands known abbreviations, and title-cases.
    """
    # Normalise camelCase to snake_case, then split.
    normalised: list[str] = []
    for index, char in enumerate(column_name):
        if char.isupper() and index > 0 and column_name[index - 1].islower():
            normalised.append("_")
        normalised.append(char)
    tokens = "".join(normalised).replace("-", "_").replace(" ", "_").split("_")

    words: list[str] = []
    for token in tokens:
        if not token:
            continue
        lowered = token.lower()
        words.append(_ABBREVIATIONS.get(lowered, token.capitalize()))
    return " ".join(words) if words else column_name


def _name_has(name: str, tokens: set[str]) -> bool:
    lowered = name.lower()
    parts = set(lowered.replace("-", "_").split("_"))
    return any(tok in parts or tok in lowered for tok in tokens)


# ============================================================
# COLUMN CLASSIFICATION
# ============================================================


def classify_column(
    column_name: str, values: list[Any]
) -> tuple[str, float, str, str]:
    """Classify a single column deterministically from its name and values.

    Returns:
        (classification, confidence, reasoning, evidence)
        classification is one of: Identifier, Timestamp, Boolean, Financial,
        Measure, Geographic, Categorical, Text, Unknown.
    """
    non_null = _non_null(values)
    if not non_null:
        return ("Unknown", 0.3, "No non-null sample values available.", "Column empty in sample.")

    distinct = len(set(str(v).strip() for v in non_null))
    uniqueness = distinct / len(non_null)
    numeric_frac = _fraction(non_null, _is_number)
    date_frac = _fraction(non_null, _is_date)
    bool_frac = _fraction(non_null, lambda v: str(v).strip().lower() in _TRUE_FALSE)

    # 1. Identifier: id-like name AND highly unique.
    if _name_has(column_name, _ID_TOKENS) and uniqueness >= 0.9:
        return (
            "Identifier",
            round(min(0.99, 0.6 + uniqueness * 0.39), 2),
            "Name matches an identifier token and values are near-unique.",
            f"{distinct}/{len(non_null)} distinct values.",
        )

    # 2. Timestamp: date-like name or values parse as dates.
    if _name_has(column_name, _TIME_TOKENS) or date_frac >= 0.7:
        conf = max(date_frac, 0.7 if _name_has(column_name, _TIME_TOKENS) else 0.0)
        return (
            "Timestamp",
            round(min(0.99, 0.6 + conf * 0.39), 2),
            "Name or values indicate temporal data.",
            f"{date_frac:.0%} of values parse as dates.",
        )

    # 3. Boolean: at most two distinct truthy/falsy values.
    if distinct <= 2 and bool_frac >= 0.9:
        return (
            "Boolean",
            0.9,
            "Only two distinct boolean-like values present.",
            f"Distinct values: {sorted(set(str(v).strip().lower() for v in non_null))}.",
        )

    # 4. Numeric: financial vs generic measure.
    if numeric_frac >= 0.8:
        if _name_has(column_name, _FINANCIAL_TOKENS):
            classification = "Financial"
            reasoning = "Numeric values with a monetary/financial name token."
        else:
            classification = "Measure"
            reasoning = "Majority of values are numeric and continuous."
        return (
            classification,
            round(min(0.99, 0.55 + numeric_frac * 0.44), 2),
            reasoning,
            f"{numeric_frac:.0%} of values are numeric.",
        )

    # 5. Geographic.
    if _name_has(column_name, _GEO_TOKENS):
        return (
            "Geographic",
            0.8,
            "Name indicates a geographic attribute.",
            f"Column '{column_name}' matches a geographic token.",
        )

    # 6. Categorical: low-cardinality strings.
    if distinct <= 20 and uniqueness < 0.5:
        return (
            "Categorical",
            round(min(0.95, 0.6 + (1 - uniqueness) * 0.35), 2),
            "Low-cardinality repeated string values.",
            f"{distinct} distinct categories across {len(non_null)} rows.",
        )

    # 7. Text fallback.
    return (
        "Text",
        0.6,
        "High-cardinality free-text values.",
        f"{distinct}/{len(non_null)} distinct values.",
    )


def _detect_industry(columns: list[str]) -> tuple[str, float]:
    """Score column names against sector keyword dictionaries."""
    scores: dict[str, int] = {}
    joined = " ".join(c.lower() for c in columns)
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for kw in keywords if kw in joined)

    best_industry = max(scores, key=lambda k: scores[k])
    best_score = scores[best_industry]
    if best_score == 0:
        return ("General", 0.4)
    # Confidence scales with number of matched keywords, capped.
    confidence = min(0.95, 0.55 + best_score * 0.1)
    return (best_industry, round(confidence, 2))


def _derive_entities(columns: list[str], classifications: dict[str, str]) -> list[str]:
    """Derive conceptual entities from identifier columns and known nouns."""
    entities: list[str] = []
    for col in columns:
        if classifications.get(col) == "Identifier":
            label = humanize_label(col)
            # Strip a trailing "Identifier"/"Id" to name the entity.
            for suffix in (" Identifier", " Id", " Number", " Code"):
                if label.endswith(suffix):
                    label = label[: -len(suffix)].strip()
            if label:
                entities.append(label)
    # De-duplicate preserving order.
    seen: set[str] = set()
    unique = [e for e in entities if not (e in seen or seen.add(e))]
    return unique or ["Record"]


# ============================================================
# PUBLIC ENTRY POINTS
# ============================================================


def infer_dataset_understanding(
    dataset_name: str, columns: list[str], sample_rows: list[dict[str, Any]]
) -> DatasetUnderstandingLLMResponse:
    """Produce the dataset-understanding structure the Data Engineer expects."""
    column_items: list[ColumnUnderstandingItem] = []
    classifications: dict[str, str] = {}
    assumptions: list[str] = []

    for col in columns:
        values = [row.get(col) for row in sample_rows]
        classification, confidence, reasoning, evidence = classify_column(col, values)
        classifications[col] = classification
        if classification == "Unknown":
            assumptions.append(f"Column '{col}' could not be classified from the sample.")
        column_items.append(
            ColumnUnderstandingItem(
                column_name=col,
                business_meaning=humanize_label(col),
                classification=classification,
                confidence=confidence,
                reasoning=reasoning,
                evidence=evidence,
            )
        )

    industry, industry_conf = _detect_industry(columns)
    domain, process = _DOMAIN_BY_INDUSTRY.get(industry, _DOMAIN_BY_INDUSTRY["General"])
    entities = _derive_entities(columns, classifications)

    col_conf = [c.confidence for c in column_items]
    overall = round(
        (sum(col_conf) / len(col_conf) * 0.7 + industry_conf * 0.3) if col_conf else industry_conf,
        2,
    )

    primary_entity = entities[0] if entities else "record"
    return DatasetUnderstandingLLMResponse(
        estimated_industry=industry,
        estimated_business_domain=domain,
        estimated_business_process=process,
        row_representation=f"A single {primary_entity.lower()} record from '{dataset_name}'.",
        detected_entities=entities,
        columns=column_items,
        overall_confidence=overall,
        assumptions=assumptions,
    )


def infer_analyst_framing(
    dataset_name: str, columns: list[str], sample_rows: list[dict[str, Any]]
) -> AnalystLLMResponse:
    """Produce KPI and business-question framing from real column semantics."""
    classifications: dict[str, str] = {}
    for col in columns:
        values = [row.get(col) for row in sample_rows]
        classifications[col], *_ = classify_column(col, values)

    measures = [c for c in columns if classifications[c] in ("Measure", "Financial")]
    financials = [c for c in columns if classifications[c] == "Financial"]
    identifiers = [c for c in columns if classifications[c] == "Identifier"]
    dimensions = [c for c in columns if classifications[c] in ("Categorical", "Geographic")]
    timestamps = [c for c in columns if classifications[c] == "Timestamp"]

    kpis: list[KPIMetadata] = []
    for col in measures[:6]:
        label = humanize_label(col)
        kpis.append(
            KPIMetadata(
                kpi_name=f"Average {label}",
                description=f"Mean value of the '{label}' measure across all records.",
                required_columns=[col],
                aggregation_type="AVERAGE",
                business_purpose=f"Benchmark overall {label.lower()} performance.",
                confidence=0.85,
            )
        )
    for col in financials[:3]:
        label = humanize_label(col)
        kpis.append(
            KPIMetadata(
                kpi_name=f"Total {label}",
                description=f"Sum of the '{label}' financial measure.",
                required_columns=[col],
                aggregation_type="SUM",
                business_purpose=f"Track cumulative {label.lower()}.",
                confidence=0.85,
            )
        )
    for col in identifiers[:1]:
        entity = humanize_label(col).replace(" Identifier", "").replace(" Id", "").strip() or "Record"
        kpis.append(
            KPIMetadata(
                kpi_name=f"Total {entity} Count",
                description=f"Distinct count of {entity.lower()} records.",
                required_columns=[col],
                aggregation_type="COUNT",
                business_purpose=f"Measure the population size of {entity.lower()}s.",
                confidence=0.9,
            )
        )

    questions: list[BusinessQuestion] = []
    for col in measures[:4]:
        label = humanize_label(col)
        questions.append(
            BusinessQuestion(
                question_text=f"What is the average {label.lower()}?",
                priority="High",
                confidence=0.85,
                required_columns=[col],
                reasoning=f"'{label}' is a core numeric measure summarising performance.",
            )
        )
    if measures and dimensions:
        m_label = humanize_label(measures[0])
        d_label = humanize_label(dimensions[0])
        questions.append(
            BusinessQuestion(
                question_text=f"How does {m_label.lower()} vary across {d_label.lower()}?",
                priority="Medium",
                confidence=0.75,
                required_columns=[measures[0], dimensions[0]],
                reasoning=f"Segmenting {m_label.lower()} by {d_label.lower()} exposes group-level gaps.",
            )
        )
    if measures and timestamps:
        m_label = humanize_label(measures[0])
        t_label = humanize_label(timestamps[0])
        questions.append(
            BusinessQuestion(
                question_text=f"How does {m_label.lower()} trend over {t_label.lower()}?",
                priority="Medium",
                confidence=0.7,
                required_columns=[measures[0], timestamps[0]],
                reasoning="A temporal column enables trend analysis of the measure.",
            )
        )

    warnings: list[str] = []
    if not measures:
        warnings.append("No numeric measures detected; quantitative KPIs are limited.")
    if not dimensions:
        warnings.append("No categorical dimensions detected; segmentation is limited.")

    if kpis:
        overall = round(sum(k.confidence for k in kpis) / len(kpis), 2)
    else:
        overall = 0.4

    return AnalystLLMResponse(
        discovered_kpis=kpis,
        business_questions=questions,
        overall_confidence=overall,
        warnings=warnings,
    )

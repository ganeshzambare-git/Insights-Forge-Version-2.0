"""
Insight Forge V2 — AI Utilities and Helpers.

Provides helper functions for serialization, confidence metrics, and evidence lists.
"""

import json
from typing import Any
from app.ai.evidence.model import Evidence
from app.ai.schemas.confidence import ConfidenceModel


def calculate_average_confidence(confidences: list[ConfidenceModel]) -> float:
    """Compute the average confidence score across a collection of measurements.

    Args:
        confidences: List of ConfidenceModel instances.

    Returns:
        The average confidence score (0.0 if empty).
    """
    if not confidences:
        return 0.0
    return sum(c.confidence_score for c in confidences) / len(confidences)


def map_score_to_categorical_level(score: float) -> str:
    """Determine category label matching a numerical confidence percentage.

    Args:
        score: Numerical score between 0.0 and 1.0.

    Returns:
        Categorical string ('HIGH', 'MEDIUM', or 'LOW').
    """
    if score >= 0.8:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


def filter_evidence_by_status(evidence_list: list[Evidence], status: str) -> list[Evidence]:
    """Filter evidence items matching a given verification status.

    Args:
        evidence_list: List of Evidence objects.
        status: The target status string.
    """
    return [e for e in evidence_list if e.validation_status.upper() == status.upper()]


def safe_serialize_json(data: Any) -> str:
    """Safely serialize an object/dictionary into structured JSON.

    Handles datetime or custom structures via default mapping fallback.
    """
    try:
        if hasattr(data, "model_dump"):
            return json.dumps(data.model_dump(), default=str)
        return json.dumps(data, default=str)
    except Exception:
        return str(data)


def deduplicate_by_title(items: list[Any]) -> list[Any]:
    """Remove items with duplicate title or issue_type fields, preserving order."""
    seen = set()
    unique_items = []
    for item in items:
        title = None
        if hasattr(item, "title"):
            title = getattr(item, "title")
        elif isinstance(item, dict) and "title" in item:
            title = item["title"]
        elif hasattr(item, "issue_type"):
            title = getattr(item, "issue_type")
        elif isinstance(item, dict) and "issue_type" in item:
            title = item["issue_type"]
            
        if title is not None:
            if title not in seen:
                seen.add(title)
                unique_items.append(item)
        else:
            unique_items.append(item)
    return unique_items


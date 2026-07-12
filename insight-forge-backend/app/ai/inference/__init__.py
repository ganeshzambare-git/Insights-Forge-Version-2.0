"""
Insight Forge V2 — Deterministic Inference Package.

Provides pure-Python, rule-based inference of dataset semantics, column
classifications, and KPI framing. Replaces external LLM calls with reproducible
heuristics computed directly from the uploaded data. No network or model access.
"""

from app.ai.inference.heuristics import (
    infer_dataset_understanding,
    infer_analyst_framing,
    classify_column,
    humanize_label,
)

__all__ = [
    "infer_dataset_understanding",
    "infer_analyst_framing",
    "classify_column",
    "humanize_label",
]

"""Run the cleaning benchmark with duplicate-safe, key-based accuracy metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ingestion.quality_pipeline import run_cleaning_pipeline


def _dedupe_for_comparison(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Keep one deterministic row per business key without changing pipeline output."""
    missing = [key for key in keys if key not in frame.columns]
    if missing:
        raise KeyError(f"Comparison keys missing from dataset: {missing}")
    return frame.drop_duplicates(subset=keys, keep="first").copy()


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    benchmark = root / "InsightForge_Benchmark_Dataset"
    raw = pd.read_excel(benchmark / "students_raw_10000.xlsx")
    expected = pd.read_excel(benchmark / "students_clean_expected.xlsx")
    result = run_cleaning_pipeline(raw)

    keys = ["Student_ID", "Semester"]
    cleaned = _dedupe_for_comparison(result.clean, keys)
    expected = _dedupe_for_comparison(expected, keys)
    expected_keyed = expected.set_index(keys).sort_index()
    cleaned_keyed = cleaned.set_index(keys).sort_index()
    common = expected_keyed.index.intersection(cleaned_keyed.index)
    columns = [column for column in expected_keyed.columns.intersection(cleaned_keyed.columns)]

    accuracy = 0.0
    if len(common) and columns:
        left = expected_keyed.loc[common, columns].astype(str)
        right = cleaned_keyed.loc[common, columns].astype(str)
        accuracy = (left.to_numpy() == right.to_numpy()).mean() * 100

    total = len(result.clean) + len(result.review) + len(result.dead_letter)
    if total != len(raw):
        raise RuntimeError(f"Partition invariant failed: {total} output rows for {len(raw)} input rows")
    print(f"Clean: {len(result.clean)}")
    print(f"Dead-letter: {len(result.dead_letter)}")
    print(f"Review: {len(result.review)}")
    print(f"Compliance: {result.compliance:.2f}%")
    print(f"Matched records after dedupe: {len(common)}")
    print(f"Columns compared: {len(columns)}")
    print(f"Cell accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    main()

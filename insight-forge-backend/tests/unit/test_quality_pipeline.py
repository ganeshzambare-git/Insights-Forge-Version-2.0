"""Focused contracts for the ingestion cleaning pipeline."""

import pandas as pd

from app.ingestion.quality_pipeline import (
    create_review_queue,
    process_review_decision,
    run_cleaning_pipeline,
)


def test_pipeline_normalizes_and_routes_invalid_records() -> None:
    result = run_cleaning_pipeline(pd.DataFrame([
        {"Student Email": "a@gmial.com", "Cohort Code": "CSE-A", "Marks": "105", "Attendance %": "90", "Course": "btech", "Branch": "CSE"},
        {"Student Email": "invalid", "Cohort Code": "CSE-A", "Marks": "-5", "Attendance %": "90", "Course": "B.Tech", "Branch": "CSE"},
    ]))
    assert len(result.clean) == 1
    assert len(result.dead_letter) == 1
    assert result.clean.loc[0, "email"] == "a@gmail.com"
    assert result.clean.loc[0, "grade"] == 100


def test_review_decision_marks_validated_record() -> None:
    result = run_cleaning_pipeline(pd.DataFrame([
        {"Student Email": "a@example.com", "Cohort Code": "CSE-A", "Marks": "88", "Attendance %": "91", "Phone": "123"},
    ]))
    queue = create_review_queue(result)
    assert len(queue) == 1
    updated = process_review_decision(queue.iloc[0].to_dict(), "edit", {"phone": "9876543210"})
    assert updated["review_status"] == "Validated"
    assert updated["_confidence"] == 1.0

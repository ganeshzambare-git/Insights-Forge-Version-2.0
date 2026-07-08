from app.models import CoachingIntervention, StudentMetric


def test_student_metric_exact_columns() -> None:
    assert list(StudentMetric.__table__.columns.keys()) == [
        "metric_id",
        "tenant_id",
        "student_user_id",
        "cohort_id",
        "raw_average_grade",
        "normalized_grade_score",
        "attendance_percentage",
        "success_indicator_status",
        "reporting_period",
    ]


def test_student_metric_delete_rules() -> None:
    tenant_fk = next(iter(StudentMetric.__table__.c.tenant_id.foreign_keys))
    student_fk = next(iter(StudentMetric.__table__.c.student_user_id.foreign_keys))
    cohort_fk = next(iter(StudentMetric.__table__.c.cohort_id.foreign_keys))

    assert tenant_fk.ondelete == "RESTRICT"
    assert student_fk.ondelete == "CASCADE"
    assert cohort_fk.ondelete == "RESTRICT"


def test_student_metric_has_locked_indexes() -> None:
    names = {index.name for index in StudentMetric.__table__.indexes}

    assert "ix_student_metrics_tenant_cohort_status" in names
    assert "ix_student_metrics_tenant_grade" in names


def test_coaching_intervention_exact_columns() -> None:
    assert list(CoachingIntervention.__table__.columns.keys()) == [
        "intervention_id",
        "tenant_id",
        "student_user_id",
        "faculty_user_id",
        "intervention_notes",
        "recorded_timestamp",
    ]


def test_coaching_intervention_delete_rules() -> None:
    tenant_fk = next(
        iter(CoachingIntervention.__table__.c.tenant_id.foreign_keys)
    )
    student_fk = next(
        iter(CoachingIntervention.__table__.c.student_user_id.foreign_keys)
    )
    faculty_fk = next(
        iter(CoachingIntervention.__table__.c.faculty_user_id.foreign_keys)
    )

    assert tenant_fk.ondelete == "RESTRICT"
    assert student_fk.ondelete == "RESTRICT"
    assert faculty_fk.ondelete == "RESTRICT"


def test_coaching_intervention_has_locked_index() -> None:
    names = {index.name for index in CoachingIntervention.__table__.indexes}

    assert "ix_coaching_interventions_tenant_student_recorded" in names
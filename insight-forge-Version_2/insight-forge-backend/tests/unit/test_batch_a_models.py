from sqlalchemy.dialects.postgresql import INET

from app.models import Cohort, Session, User


def test_user_exact_columns() -> None:
    assert list(User.__table__.columns.keys()) == [
        "user_id",
        "tenant_id",
        "corporate_email",
        "password_hash",
        "assigned_role",
        "is_mfa_enabled",
        "totp_secret",
    ]


def test_user_tenant_delete_rule() -> None:
    fk = next(iter(User.__table__.c.tenant_id.foreign_keys))
    assert fk.ondelete == "RESTRICT"


def test_user_has_role_check_constraint() -> None:
    names = {constraint.name for constraint in User.__table__.constraints}
    assert "ck_users_assigned_role" in names


def test_session_exact_columns() -> None:
    assert list(Session.__table__.columns.keys()) == [
        "session_id",
        "user_id",
        "tenant_id",
        "jwt_jti",
        "expires_at",
        "ingress_ip",
    ]


def test_session_delete_rules() -> None:
    user_fk = next(iter(Session.__table__.c.user_id.foreign_keys))
    tenant_fk = next(iter(Session.__table__.c.tenant_id.foreign_keys))

    assert user_fk.ondelete == "CASCADE"
    assert tenant_fk.ondelete == "RESTRICT"


def test_session_uses_native_inet() -> None:
    assert isinstance(Session.__table__.c.ingress_ip.type, INET)


def test_session_jti_is_unique() -> None:
    assert Session.__table__.c.jwt_jti.unique is True


def test_cohort_exact_columns() -> None:
    assert list(Cohort.__table__.columns.keys()) == [
        "cohort_id",
        "tenant_id",
        "cohort_code",
        "department_scope",
    ]


def test_cohort_tenant_delete_rule() -> None:
    fk = next(iter(Cohort.__table__.c.tenant_id.foreign_keys))
    assert fk.ondelete == "RESTRICT"
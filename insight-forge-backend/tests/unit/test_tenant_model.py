import uuid

from app.models import Tenant


def test_tenant_table_name() -> None:
    assert Tenant.__tablename__ == "tenants"


def test_tenant_has_exact_locked_columns() -> None:
    assert list(Tenant.__table__.columns.keys()) == [
        "tenant_id",
        "tenant_slug",
        "tenant_name",
        "created_at",
    ]


def test_tenant_id_is_primary_key() -> None:
    assert Tenant.__table__.c.tenant_id.primary_key is True


def test_tenant_slug_is_required_and_unique() -> None:
    column = Tenant.__table__.c.tenant_slug

    assert column.nullable is False
    assert column.unique is True


def test_tenant_name_is_required() -> None:
    assert Tenant.__table__.c.tenant_name.nullable is False


def test_created_at_is_required_and_server_generated() -> None:
    column = Tenant.__table__.c.created_at

    assert column.nullable is False
    assert column.server_default is not None


def test_tenant_can_be_constructed() -> None:
    tenant_id = uuid.uuid4()

    tenant = Tenant(
        tenant_id=tenant_id,
        tenant_slug="data-dragons",
        tenant_name="Data Dragons University",
    )

    assert tenant.tenant_id == tenant_id
    assert tenant.tenant_slug == "data-dragons"
    assert tenant.tenant_name == "Data Dragons University"

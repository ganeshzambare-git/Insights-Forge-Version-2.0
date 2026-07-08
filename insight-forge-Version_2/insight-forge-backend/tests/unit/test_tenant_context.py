import uuid
from unittest.mock import MagicMock

from app.db.tenant_context import set_tenant_context


def test_set_tenant_context_executes_transaction_local_setting() -> None:
    session = MagicMock()
    tenant_id = uuid.uuid4()

    set_tenant_context(session, tenant_id)

    session.execute.assert_called_once()

    statement, parameters = session.execute.call_args.args

    assert "set_config" in str(statement)
    assert "app.current_tenant_id" in str(statement)
    assert parameters == {"tenant_id": str(tenant_id)}
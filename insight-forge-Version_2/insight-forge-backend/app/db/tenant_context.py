import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session


def set_tenant_context(
    session: Session,
    tenant_id: uuid.UUID,
) -> None:
    """
    Set the validated tenant UUID for the current database transaction.

    PostgreSQL RLS policies read this value through:
    current_setting('app.current_tenant_id', true)

    SET LOCAL ensures the value disappears automatically when the
    transaction commits or rolls back.
    """
    session.execute(
        text(
            "SELECT set_config("
            "'app.current_tenant_id', "
            ":tenant_id, "
            "true"
            ")"
        ),
        {"tenant_id": str(tenant_id)},
    )
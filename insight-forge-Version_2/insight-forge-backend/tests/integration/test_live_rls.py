import uuid

import psycopg

from app.core.config import settings


def test_live_tenant_rls_isolation() -> None:
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    try:
        # ------------------------------------------------------------
        # PHASE 1: Seed test data using the migration/owner connection
        # ------------------------------------------------------------
        with psycopg.connect(
            settings.MIGRATION_DATABASE_URL
        ) as owner:
            with owner.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tenants (
                        tenant_id,
                        tenant_slug,
                        tenant_name
                    )
                    VALUES
                        (%s, %s, %s),
                        (%s, %s, %s)
                    """,
                    (
                        tenant_a,
                        f"rls-a-{tenant_a.hex[:8]}",
                        "RLS Test Tenant A",
                        tenant_b,
                        f"rls-b-{tenant_b.hex[:8]}",
                        "RLS Test Tenant B",
                    ),
                )

                cur.execute(
                    """
                    INSERT INTO cohorts (
                        tenant_id,
                        cohort_code,
                        department_scope
                    )
                    VALUES
                        (%s, %s, %s),
                        (%s, %s, %s)
                    """,
                    (
                        tenant_a,
                        "RLS-A",
                        "Test",
                        tenant_b,
                        "RLS-B",
                        "Test",
                    ),
                )

        # ------------------------------------------------------------
        # PHASE 2: Tenant A must see only Tenant A's row
        # ------------------------------------------------------------
        with psycopg.connect(
            settings.DATABASE_URL
        ) as runtime:
            with runtime.cursor() as cur:
                cur.execute(
                    """
                    SELECT set_config(
                        'app.current_tenant_id',
                        %s,
                        true
                    )
                    """,
                    (str(tenant_a),),
                )

                cur.execute(
                    """
                    SELECT tenant_id
                    FROM cohorts
                    ORDER BY cohort_code
                    """
                )

                visible_rows = cur.fetchall()

                assert visible_rows == [(tenant_a,)]

        # ------------------------------------------------------------
        # PHASE 3: Tenant B must see only Tenant B's row
        # ------------------------------------------------------------
        with psycopg.connect(
            settings.DATABASE_URL
        ) as runtime:
            with runtime.cursor() as cur:
                cur.execute(
                    """
                    SELECT set_config(
                        'app.current_tenant_id',
                        %s,
                        true
                    )
                    """,
                    (str(tenant_b),),
                )

                cur.execute(
                    """
                    SELECT tenant_id
                    FROM cohorts
                    ORDER BY cohort_code
                    """
                )

                visible_rows = cur.fetchall()

                assert visible_rows == [(tenant_b,)]

        # ------------------------------------------------------------
        # PHASE 4: No tenant context must expose zero tenant rows
        # ------------------------------------------------------------
        with psycopg.connect(
            settings.DATABASE_URL
        ) as runtime:
            with runtime.cursor() as cur:
                cur.execute(
                    """
                    SELECT tenant_id
                    FROM cohorts
                    WHERE tenant_id IN (%s, %s)
                    """,
                    (
                        tenant_a,
                        tenant_b,
                    ),
                )

                visible_rows = cur.fetchall()

                assert visible_rows == []

        # ------------------------------------------------------------
        # PHASE 5: Tenant A must not be able to insert Tenant B data
        # ------------------------------------------------------------
        with psycopg.connect(
            settings.DATABASE_URL
        ) as runtime:
            with runtime.cursor() as cur:
                cur.execute(
                    """
                    SELECT set_config(
                        'app.current_tenant_id',
                        %s,
                        true
                    )
                    """,
                    (str(tenant_a),),
                )

                try:
                    cur.execute(
                        """
                        INSERT INTO cohorts (
                            tenant_id,
                            cohort_code,
                            department_scope
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (
                            tenant_b,
                            "RLS-BLOCKED",
                            "Test",
                        ),
                    )
                except psycopg.errors.InsufficientPrivilege:
                    runtime.rollback()
                else:
                    raise AssertionError(
                        "RLS security failure: Tenant A was able "
                        "to insert a Tenant B row."
                    )

    finally:
        # ------------------------------------------------------------
        # CLEANUP: Always remove temporary test data
        # ------------------------------------------------------------
        with psycopg.connect(
            settings.MIGRATION_DATABASE_URL
        ) as owner:
            with owner.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM cohorts
                    WHERE tenant_id IN (%s, %s)
                    """,
                    (
                        tenant_a,
                        tenant_b,
                    ),
                )

                cur.execute(
                    """
                    DELETE FROM tenants
                    WHERE tenant_id IN (%s, %s)
                    """,
                    (
                        tenant_a,
                        tenant_b,
                    ),
                )
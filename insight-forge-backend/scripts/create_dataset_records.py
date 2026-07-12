"""
Insight Forge V2 — Additive DDL for the ``dataset_records`` table.

The live database was provisioned by a sibling codebase whose Alembic revision is
not present in this repository, so ``alembic upgrade`` cannot chain onto it. The
``datasets`` table already exists there; only ``dataset_records`` is missing.

This script creates that one additive table (idempotently) plus its index and
tenant-isolation RLS policy, without touching any existing table or Alembic state.
"""

from urllib.parse import urlparse

import psycopg

from app.core.config import settings

DDL = """
CREATE TABLE IF NOT EXISTS dataset_records (
    record_id  BIGINT GENERATED ALWAYS AS IDENTITY,
    dataset_id UUID NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    tenant_id  UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE RESTRICT,
    row_index  INTEGER NOT NULL,
    payload    JSONB NOT NULL,
    CONSTRAINT pk_dataset_records PRIMARY KEY (record_id)
);

CREATE INDEX IF NOT EXISTS ix_dataset_records_dataset_id_row_index
    ON dataset_records (dataset_id, row_index);

ALTER TABLE dataset_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON dataset_records;
CREATE POLICY tenant_isolation_policy ON dataset_records
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
"""


def main() -> None:
    migration_url = (settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL)
    migration_url = migration_url.replace("+psycopg", "").replace("+asyncpg", "")
    runtime_url = settings.DATABASE_URL.replace("+psycopg", "").replace("+asyncpg", "")
    runtime_user = urlparse(runtime_url).username

    with psycopg.connect(migration_url) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            # The table is owned by the migration role; grant the restricted
            # runtime role access to the table and its identity sequence.
            if runtime_user:
                cur.execute(
                    f'GRANT SELECT, INSERT, UPDATE, DELETE ON dataset_records TO "{runtime_user}";'
                )
                cur.execute(
                    f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{runtime_user}";'
                )
        conn.commit()
    print(
        f"dataset_records table ensured with RLS policy; privileges granted to '{runtime_user}'."
    )


if __name__ == "__main__":
    main()

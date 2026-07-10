"""
Insight Forge V2 — Migration Verification Helper.

Queries the active database to ensure all expected tables and Alembic tracking rows exist.
"""

import sys
import psycopg

from app.core.config import settings


def verify_migrations() -> None:
    """Query information_schema and alembic_version tables to verify migration success."""
    db_url = settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL
    if not db_url:
        print("Error: No database connection URL configured.")
        sys.exit(1)

    if "+psycopg" in db_url:
        db_url = db_url.replace("+psycopg", "")

    print("Verifying database schema migrations...")
    try:
        conn = psycopg.connect(db_url)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
                """
            )
            tables = {row[0] for row in cur.fetchall()}

            expected = {
                "tenants",
                "users",
                "sessions",
                "cohorts",
                "student_metrics",
                "coaching_interventions",
                "alembic_version",
            }

            missing = expected - tables
            if missing:
                print(f"Verification failed: missing tables: {missing}", file=sys.stderr)
                sys.exit(1)

            cur.execute("SELECT version_num FROM alembic_version;")
            version = cur.fetchone()
            if not version:
                print("Verification failed: alembic_version table is empty.", file=sys.stderr)
                sys.exit(1)

            print(f"Schema verification succeeded. Current Alembic version: {version[0]}")
            print(f"Confirmed presence of expected tables: {expected}")
        conn.close()
    except Exception as e:
        print(f"Verification encountered an error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    verify_migrations()

"""
Insight Forge V2 — Row-Level Security Verification Helper.

Queries PostgreSQL catalogs to verify if RLS is enabled on target database tables.
"""

import sys
import psycopg

from app.core.config import settings


def verify_rls() -> None:
    """Query pg_class and pg_namespace to assert relrowsecurity is enabled on tables."""
    db_url = settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL
    if not db_url:
        print("Error: No database connection URL configured.")
        sys.exit(1)

    if "+psycopg" in db_url:
        db_url = db_url.replace("+psycopg", "")

    print("Verifying PostgreSQL Row-Level Security (RLS) activation...")
    try:
        conn = psycopg.connect(db_url)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.relname, c.relrowsecurity 
                FROM pg_class c 
                JOIN pg_namespace n ON n.oid = c.relnamespace 
                WHERE n.nspname = 'public' AND c.relname IN (
                    'users', 'sessions', 'cohorts', 'student_metrics', 'coaching_interventions'
                );
                """
            )
            results = cur.fetchall()

            if not results:
                print("Warning: Target tables not found. Ensure migrations have run.")
                sys.exit(1)

            rls_enabled = []
            rls_disabled = []
            for name, security_active in results:
                if security_active:
                    rls_enabled.append(name)
                else:
                    rls_disabled.append(name)

            print(f"RLS is ENABLED on: {rls_enabled}")
            if rls_disabled:
                print(f"Warning: RLS is NOT enabled on: {rls_disabled}")
            else:
                print("Confirmed all target tables have RLS enabled.")
        conn.close()
    except Exception as e:
        print(f"Error checking RLS status: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    verify_rls()

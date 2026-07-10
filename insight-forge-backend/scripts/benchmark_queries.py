"""
Insight Forge V2 — Database Query Benchmarks.

Runs connection tests and tracks latency on key table count queries.
"""

import sys
import time
import psycopg

from app.core.config import settings


def benchmark_queries() -> None:
    """Execute count queries on tenants/users and print timings."""
    db_url = settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL
    if not db_url:
        print("Error: No database connection URL configured.")
        sys.exit(1)

    if "+psycopg" in db_url:
        db_url = db_url.replace("+psycopg", "")

    print("Running database query benchmarks...")
    try:
        conn = psycopg.connect(db_url)
        with conn.cursor() as cur:
            start = time.perf_counter()

            cur.execute("SELECT count(*) FROM tenants;")
            tenant_count = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM users;")
            user_count = cur.fetchone()[0]

            end = time.perf_counter()
            latency = (end - start) * 1000  # ms
            print(f"Database query benchmark finished in {latency:.2f}ms")
            print(f"Stats: Tenants: {tenant_count}, Users: {user_count}")
        conn.close()
    except Exception as e:
        print(f"Benchmark encountered an error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    benchmark_queries()

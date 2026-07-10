"""
Insight Forge V2 — Developer Bootstrap Script.

Coordinates database creation, Alembic schema migrations, and idempotent data seeding.
"""

import subprocess
import sys
from urllib.parse import urlparse

import psycopg

from app.core.config import settings


def run_command(command: list[str]) -> None:
    """Execute a shell command, printing output and checking exit status."""
    print(f"\n---> Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Bootstrap step failed: {e}", file=sys.stderr)
        sys.exit(e.returncode or 1)


def grant_permissions() -> None:
    """Grant table and sequence permissions to the application runtime user."""
    runtime_url = settings.DATABASE_URL
    migration_url = settings.MIGRATION_DATABASE_URL or runtime_url

    if "+psycopg" in runtime_url:
        runtime_url = runtime_url.replace("+psycopg", "")
    if "+psycopg" in migration_url:
        migration_url = migration_url.replace("+psycopg", "")

    runtime_parsed = urlparse(runtime_url)
    runtime_user = runtime_parsed.username

    if runtime_user:
        print(f"\n---> Granting database permissions to runtime user '{runtime_user}'...")
        try:
            with psycopg.connect(migration_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{runtime_user}";')
                    cur.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{runtime_user}";')
                conn.commit()
            print("Permissions granted successfully.")
        except Exception as e:
            print(f"Warning: Failed to grant permissions: {e}", file=sys.stderr)


def bootstrap() -> None:
    """Execute database check, Alembic upgrades, and database seeding sequentially."""
    print("=============================================================")
    print("INSIGHT FORGE V2.2 — DEVELOPER BOOTSTRAP SYSTEM")
    print("=============================================================")

    # 1. Create PostgreSQL database
    run_command([sys.executable, "-m", "scripts.create_database"])

    # 2. Upgrade database to head migrations
    run_command([sys.executable, "-m", "alembic", "upgrade", "head"])

    # 3. Grant database permissions to restricted role
    grant_permissions()

    # 4. Seed default Tenant and Admin User
    run_command([sys.executable, "-m", "scripts.seed_database"])

    print("\n=============================================================")
    print("BOOTSTRAP COMPLETED SUCCESSFULLY")
    print("=============================================================")


if __name__ == "__main__":
    bootstrap()

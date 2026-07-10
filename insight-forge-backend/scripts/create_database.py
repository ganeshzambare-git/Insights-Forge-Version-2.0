"""
Insight Forge V2 — Database Creation Helper.

Checks if the target PostgreSQL database exists and creates it if missing.
"""

import sys
from urllib.parse import urlparse, urlunparse
import psycopg

from app.core.config import settings


def create_database() -> None:
    """Connect to default 'postgres' db and execute CREATE DATABASE if target is missing."""
    db_url = settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL
    if not db_url:
        print("Error: Neither MIGRATION_DATABASE_URL nor DATABASE_URL is configured.")
        sys.exit(1)

    # Strip async driver prefix if present
    if "+psycopg" in db_url:
        db_url = db_url.replace("+psycopg", "")

    parsed = urlparse(db_url)
    target_db = parsed.path.lstrip("/")

    if not target_db:
        print("Error: Target database name not specified in connection URL.")
        sys.exit(1)

    # Construct url to default postgres database
    postgres_parsed = parsed._replace(path="/postgres")
    postgres_url = urlunparse(postgres_parsed)

    print(f"Connecting to PostgreSQL default instance to verify database '{target_db}'...")
    try:
        conn = psycopg.connect(postgres_url, autocommit=True)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
            exists = cur.fetchone()
            if not exists:
                print(f"Database '{target_db}' not found. Creating database...")
                # Database names are quoted to prevent injection
                cur.execute(f'CREATE DATABASE "{target_db}";')
                print(f"Database '{target_db}' created successfully.")
            else:
                print(f"Database '{target_db}' already exists.")
        conn.close()
    except Exception as e:
        print(f"Error during database check/creation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    create_database()

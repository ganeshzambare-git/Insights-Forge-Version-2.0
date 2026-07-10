"""
Create or rotate a local administrator login.

This is intended for development and demo environments where an operator needs
fresh credentials for the web login screen.
"""

from __future__ import annotations

import asyncio
import secrets
import string
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User


TENANT_SLUG = "default-tenant"
TENANT_NAME = "Default Educational Institution"
ADMIN_EMAIL = "admin@insightforge.com"


def generate_password(length: int = 18) -> str:
    """Generate a password that satisfies the app's strength policy."""
    groups = [
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        "!@#$%^&*",
    ]
    chars = [secrets.choice(group) for group in groups]
    alphabet = "".join(groups)
    chars.extend(secrets.choice(alphabet) for _ in range(length - len(chars)))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


async def create_admin_credentials() -> tuple[str, str, str]:
    """Create or update the default tenant admin and return login details."""
    database_url = settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    password = generate_password()

    try:
        async with session_factory() as session:
            tenant_result = await session.execute(
                select(Tenant).where(Tenant.tenant_slug == TENANT_SLUG)
            )
            tenant = tenant_result.scalar_one_or_none()
            if tenant is None:
                tenant = Tenant(
                    tenant_id=uuid.uuid4(),
                    tenant_slug=TENANT_SLUG,
                    tenant_name=TENANT_NAME,
                )
                session.add(tenant)
                await session.flush()

            user_result = await session.execute(
                select(User).where(User.corporate_email == ADMIN_EMAIL)
            )
            admin_user = user_result.scalar_one_or_none()
            password_hash = hash_password(password)

            if admin_user is None:
                admin_user = User(
                    user_id=uuid.uuid4(),
                    tenant_id=tenant.tenant_id,
                    corporate_email=ADMIN_EMAIL,
                    password_hash=password_hash,
                    assigned_role="Admin",
                    is_mfa_enabled=False,
                )
                session.add(admin_user)
            else:
                admin_user.tenant_id = tenant.tenant_id
                admin_user.password_hash = password_hash
                admin_user.assigned_role = "Admin"
                admin_user.is_mfa_enabled = False

            await session.commit()
    finally:
        await engine.dispose()

    return TENANT_SLUG, ADMIN_EMAIL, password


async def main() -> None:
    tenant_slug, email, password = await create_admin_credentials()
    print(f"workspace_slug={tenant_slug}")
    print(f"username={email}")
    print(f"password={password}")
    print("mfa_pin=000000")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(main())

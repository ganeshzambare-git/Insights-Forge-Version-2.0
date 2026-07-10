"""
Insight Forge V2 — Database Seeding Script.

Idempotently seeds a default tenant and an initial administrator user.
"""

import asyncio
import sys

# Set selector event loop on Windows to support psycopg async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import hash_password

# Construct a privileged database engine for administrative seeding
migration_url = settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL
if migration_url.startswith("postgresql://"):
    migration_url = migration_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_async_engine(migration_url)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def seed_database() -> None:
    """Check for and insert default Tenant and Admin User records."""
    async with async_session_maker() as session:
        # 1. Seed Tenant
        tenant_slug = "default-tenant"
        tenant_stmt = select(Tenant).where(Tenant.tenant_slug == tenant_slug)
        result = await session.execute(tenant_stmt)
        tenant = result.scalar_one_or_none()

        if not tenant:
            print("Seeding default tenant...")
            tenant = Tenant(
                tenant_id=uuid.uuid4(),
                tenant_slug=tenant_slug,
                tenant_name="Default Educational Institution",
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            print(f"Default tenant created: {tenant.tenant_id}")
        else:
            print(f"Default tenant already exists: {tenant.tenant_id}")

        # 2. Seed Admin User
        admin_email = "admin@insightforge.com"
        user_stmt = select(User).where(User.corporate_email == admin_email)
        result = await session.execute(user_stmt)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            print("Seeding default administrator user...")
            hashed_pw = hash_password("AdminSecurePassword123!")
            admin_user = User(
                user_id=uuid.uuid4(),
                tenant_id=tenant.tenant_id,
                corporate_email=admin_email,
                password_hash=hashed_pw,
                assigned_role="Admin",
                is_mfa_enabled=False,
            )
            session.add(admin_user)
            await session.commit()
            print(f"Default admin user created: {admin_email}")
        else:
            print(f"Default admin user already exists: {admin_email}")


if __name__ == "__main__":
    asyncio.run(seed_database())

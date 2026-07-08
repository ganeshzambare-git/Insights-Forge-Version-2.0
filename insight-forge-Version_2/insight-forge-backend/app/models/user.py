import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types.encrypted import EncryptedString


class User(Base):
    """Authenticated user belonging to one institutional tenant."""

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "assigned_role IN ('Admin', 'Dean', 'Faculty', 'Student')",
            name="assigned_role",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "tenants.tenant_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    corporate_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    assigned_role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    is_mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    totp_secret: Mapped[str | None] = mapped_column(
        EncryptedString(128),
        nullable=True,
    )
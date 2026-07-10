from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins.timestamp import TimestampMixin


class TimestampedModel(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_timestamp_mixin_adds_created_at() -> None:
    assert "created_at" in TimestampedModel.__table__.columns


def test_timestamp_mixin_adds_updated_at() -> None:
    assert "updated_at" in TimestampedModel.__table__.columns


def test_timestamp_columns_are_not_nullable() -> None:
    assert TimestampedModel.__table__.c.created_at.nullable is False
    assert TimestampedModel.__table__.c.updated_at.nullable is False


def test_timestamp_columns_are_timezone_aware() -> None:
    assert TimestampedModel.__table__.c.created_at.type.timezone is True
    assert TimestampedModel.__table__.c.updated_at.type.timezone is True

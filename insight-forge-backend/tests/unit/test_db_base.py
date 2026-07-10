from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, NAMING_CONVENTION


class ExampleModel(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_base_generates_snake_case_table_name() -> None:
    assert ExampleModel.__tablename__ == "example_model"


def test_base_uses_naming_convention() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION


def test_base_repr_contains_primary_key() -> None:
    model = ExampleModel(id=101)

    assert repr(model) == "<ExampleModel(id=101)>"

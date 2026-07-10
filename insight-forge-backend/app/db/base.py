from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class inherited by every Insight Forge ORM model."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate a predictable snake_case table name from the class name."""
        name = cls.__name__

        characters: list[str] = []

        for index, character in enumerate(name):
            if character.isupper() and index > 0:
                characters.append("_")

            characters.append(character.lower())

        return "".join(characters)

    def __repr__(self) -> str:
        primary_key_values: list[str] = []

        for column in self.__table__.primary_key.columns:
            value: Any = getattr(self, column.name, None)
            primary_key_values.append(f"{column.name}={value!r}")

        values = ", ".join(primary_key_values)
        return f"<{self.__class__.__name__}({values})>"

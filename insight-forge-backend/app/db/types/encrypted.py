from __future__ import annotations

from typing import Any

from sqlalchemy import Text
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator

from app.core.security.encryption import encrypt_string, decrypt_string


class EncryptedString(TypeDecorator[str]):
    """
    Central SQLAlchemy boundary for encrypted string fields.

    The physical PostgreSQL storage type is TEXT.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(
        self,
        value: str | None,
        dialect: Dialect,
    ) -> str | None:
        if value is None:
            return None
        return encrypt_string(value)

    def process_result_value(
        self,
        value: Any,
        dialect: Dialect,
    ) -> str | None:
        if value is None:
            return None
        return decrypt_string(value)

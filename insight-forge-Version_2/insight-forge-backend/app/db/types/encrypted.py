from __future__ import annotations

from typing import Any

from sqlalchemy import Text
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator


class EncryptedString(TypeDecorator[str]):
    """
    Central SQLAlchemy boundary for encrypted string fields.

    The physical PostgreSQL storage type is TEXT.
    Encryption remains fail-closed until the cryptographic
    implementation and key-management contract are configured.
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

        raise RuntimeError(
            "EncryptedString cannot persist plaintext. "
            "Encryption infrastructure must be configured first."
        )

    def process_result_value(
        self,
        value: Any,
        dialect: Dialect,
    ) -> str | None:
        if value is None:
            return None

        raise RuntimeError(
            "EncryptedString cannot return undecrypted database values. "
            "Decryption infrastructure must be configured first."
        )
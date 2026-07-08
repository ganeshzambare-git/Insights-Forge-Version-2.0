import pytest
from sqlalchemy.dialects import postgresql

from app.db.types.encrypted import EncryptedString


def test_encrypted_string_preserves_length() -> None:
    encrypted_type = EncryptedString(128)

    assert encrypted_type.impl.length == 128


def test_encrypted_string_is_cache_safe() -> None:
    assert EncryptedString.cache_ok is True


def test_none_can_be_bound() -> None:
    encrypted_type = EncryptedString(128)

    result = encrypted_type.process_bind_param(
        None,
        postgresql.dialect(),
    )

    assert result is None


def test_plaintext_persistence_fails_closed() -> None:
    encrypted_type = EncryptedString(128)

    with pytest.raises(
        RuntimeError,
        match="cannot persist plaintext",
    ):
        encrypted_type.process_bind_param(
            "secret-value",
            postgresql.dialect(),
        )


def test_none_can_be_read() -> None:
    encrypted_type = EncryptedString(128)

    result = encrypted_type.process_result_value(
        None,
        postgresql.dialect(),
    )

    assert result is None


def test_undecrypted_database_value_fails_closed() -> None:
    encrypted_type = EncryptedString(128)

    with pytest.raises(
        RuntimeError,
        match="cannot return undecrypted",
    ):
        encrypted_type.process_result_value(
            "ciphertext-value",
            postgresql.dialect(),
        )
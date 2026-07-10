"""
Insight Forge V2 — Cryptographic Utilities.

Implements symmetric Fernet encryption and decryption for sensitive database columns.
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def get_fernet_key() -> bytes:
    """Derive a valid urlsafe base64 key from the application SECRET_KEY using SHA256."""
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_string(plaintext: str | None) -> str | None:
    """Encrypt a plaintext string using Fernet symmetric encryption."""
    if plaintext is None:
        return None
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_string(ciphertext: str | None) -> str | None:
    """Decrypt a ciphertext string back to plaintext."""
    if ciphertext is None:
        return None
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

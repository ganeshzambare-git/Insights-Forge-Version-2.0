"""
Insight Forge V2 — Password Security.

Handles password strength validation, hashing, and verification.
"""

import re
import bcrypt


def hash_password(password: str) -> str:
    """Hash a raw password string using bcrypt.

    Args:
        password: Raw password string.

    Returns:
        The encoded string password hash.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a raw password against its bcrypt hash.

    Args:
        password: Raw password input.
        hashed: Stored password hash string.

    Returns:
        True if the password is valid, otherwise False.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    """Validate that a password meets complexity rules.

    Args:
        password: Raw password input.

    Raises:
        ValidationError: If the password violates complexity constraints.
    """
    from app.services.exceptions import ValidationError
    if len(password) < 8 or len(password) > 128:
        raise ValidationError(
            "Password must be between 8 and 128 characters long.",
            error_code="password_length_invalid",
        )
    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain at least one lowercase letter.",
            error_code="password_missing_lowercase",
        )
    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain at least one uppercase letter.",
            error_code="password_missing_uppercase",
        )
    if not re.search(r"[0-9]", password):
        raise ValidationError(
            "Password must contain at least one number.",
            error_code="password_missing_number",
        )
    if not re.search(r"[^a-zA-Z0-9]", password):
        raise ValidationError(
            "Password must contain at least one special character.",
            error_code="password_missing_special",
        )

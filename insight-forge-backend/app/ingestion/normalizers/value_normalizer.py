"""Recoverable value normalization used before validation."""

import re
from typing import Any

EMAIL_DOMAINS = {"gmial.com": "gmail.com", "gamil.com": "gmail.com", "gmail.co": "gmail.com", "yhoo.com": "yahoo.com", "yahooo.com": "yahoo.com", "hotmal.com": "hotmail.com"}


def normalize_email(value: Any) -> str:
    email = str(value or "").strip().lower().replace(" ", "")
    local, separator, domain = email.partition("@")
    return f"{local}@{EMAIL_DOMAINS.get(domain, domain)}" if separator else email


def normalize_email_domain(value: str) -> str:
    return normalize_email(value)


def normalize_phone(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    digits = re.sub(r"(?:^00)?91", "", digits) if len(digits) >= 12 else digits
    return digits[-10:] if len(digits) >= 10 else digits


def _number(value: Any) -> float | None:
    try:
        return float(str(value).strip().replace("%", ""))
    except (TypeError, ValueError):
        return None


def normalize_cgpa(value: Any) -> float | None:
    number = _number(value)
    if number is not None and 10 < number <= 100:
        number /= 10
    return min(number, 10.0) if number is not None and number <= 10.5 else number


def normalize_marks(value: Any) -> float | None:
    number = _number(value)
    return min(number, 100.0) if number is not None and number <= 105 else number


def normalize_attendance(value: Any) -> float | None:
    return normalize_marks(value)

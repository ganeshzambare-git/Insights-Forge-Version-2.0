"""Configuration loading for tenant-neutral ingestion rules."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@lru_cache(maxsize=1)
def load_settings() -> dict[str, Any]:
    """Load packaged defaults; callers may layer tenant overrides on top."""
    path = Path(__file__).with_name("settings.yaml")
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source) or {}

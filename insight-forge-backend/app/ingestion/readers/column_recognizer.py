"""Stage 1 public column-recognition contract."""
from app.ingestion.quality_pipeline import normalize_header, recognize_columns

__all__ = ["normalize_header", "recognize_columns"]

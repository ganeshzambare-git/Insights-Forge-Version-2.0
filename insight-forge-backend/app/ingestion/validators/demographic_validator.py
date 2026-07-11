"""Stage 5 demographic normalization is executed by the canonical pipeline."""
from app.ingestion.quality_pipeline import run_cleaning_pipeline

__all__ = ["run_cleaning_pipeline"]

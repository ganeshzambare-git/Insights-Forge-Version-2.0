"""Stage 9 uses KNNImputer through the canonical pipeline."""
from app.ingestion.quality_pipeline import run_cleaning_pipeline
__all__ = ["run_cleaning_pipeline"]

"""Stage 10 uses IsolationForest and dead-letter routing in the canonical pipeline."""
from app.ingestion.quality_pipeline import run_cleaning_pipeline
__all__ = ["run_cleaning_pipeline"]

"""Stage 8 is centralized in the canonical pipeline to preserve audit semantics."""
from app.ingestion.quality_pipeline import run_cleaning_pipeline
__all__ = ["run_cleaning_pipeline"]

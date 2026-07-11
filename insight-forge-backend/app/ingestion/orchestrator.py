"""Public ten-stage ingestion runner."""
from app.ingestion.quality_pipeline import PipelineResult, run_cleaning_pipeline

__all__ = ["PipelineResult", "run_cleaning_pipeline"]

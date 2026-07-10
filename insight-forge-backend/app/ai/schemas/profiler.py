"""
Insight Forge V2 — Data Profiling Schemas.

Defines structured Pydantic models for column and dataset-level profiling.
"""

from typing import Any
from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    """Detailed statistical and quality profile for a single column."""

    data_type: str = Field(
        ...,
        description="Physical or inferred data type (e.g. integer, float, string, date).",
    )
    null_count: int = Field(
        ...,
        ge=0,
        description="Total number of missing or null records in this column.",
    )
    null_percentage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of missing records relative to the total rows count.",
    )
    distinct_values: list[Any] = Field(
        default_factory=list,
        description="Sample or complete list of distinct values (capped for performance).",
    )
    unique_values_count: int = Field(
        ...,
        ge=0,
        description="Number of distinct unique values (cardinality).",
    )
    duplicate_percentage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of non-unique duplicate values.",
    )
    min_value: Any = Field(None, description="Minimum value in column.")
    max_value: Any = Field(None, description="Maximum value in column.")
    mean: float | None = Field(None, description="Arithmetic mean for numeric columns.")
    median: float | None = Field(None, description="Median value for numeric columns.")
    mode: Any = Field(None, description="Most frequent value in column.")
    std_dev: float | None = Field(None, description="Standard deviation for numeric columns.")
    value_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Map of value frequencies (top 10 capped for high-cardinality).",
    )
    cardinality: int = Field(
        ...,
        ge=0,
        description="Cardinality count (identical to unique_values_count).",
    )
    entropy: float = Field(
        ...,
        ge=0.0,
        description="Shannon Entropy score representing column data diversity/chaos.",
    )
    length_min: int | None = Field(None, description="Minimum string length for text columns.")
    length_max: int | None = Field(None, description="Maximum string length for text columns.")
    length_mean: float | None = Field(None, description="Average string length for text columns.")
    pattern_consistency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of records matching a dominant text pattern format.",
    )
    type_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="System confidence in type inference (0.0 to 1.0).",
    )
    business_importance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calculated business importance level based on semantic meaning.",
    )
    overall_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Consolidated quality metric combining nulls, type checks, and errors.",
    )


class ConstraintAnalysis(BaseModel):
    """Represents a discovered database or business rule constraint candidate."""

    constraint_type: str = Field(
        ...,
        description="Type (PRIMARY_KEY, UNIQUE, FOREIGN_KEY, NULLABLE, CONSTANT, NEAR_CONSTANT, NUMERIC_RANGE, CATEGORICAL, DATE_FORMAT, PATTERN).",
    )
    columns: list[str] = Field(
        default_factory=list,
        description="Target columns associated with this constraint constraint.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Certainty score (0.0 to 1.0) of the constraint candidate.",
    )
    reasoning: str = Field(
        ...,
        description="Qualitative justification behind constraint inference.",
    )
    evidence: str = Field(
        ...,
        description="Traceable statistics backing the constraint discovery.",
    )


class DatasetProfile(BaseModel):
    """Consolidated statistical dataset profile and constraint registry."""

    dataset_name: str = Field(..., description="Target dataset name.")
    row_count: int = Field(..., ge=0, description="Total rows in dataset.")
    column_count: int = Field(..., ge=0, description="Total columns in dataset.")
    overall_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Aggregated dataset quality average score.",
    )
    column_profiles: dict[str, ColumnProfile] = Field(
        default_factory=dict,
        description="Map of column profiles indexed by column header.",
    )
    constraints: list[ConstraintAnalysis] = Field(
        default_factory=list,
        description="List of detected schemas or business rule constraints.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Compilation of data quality or calculation edge-case warnings.",
    )

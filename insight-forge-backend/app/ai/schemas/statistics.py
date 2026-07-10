"""
Insight Forge V2 — Statistical Analysis Schemas.

Defines Pydantic models for statistical tests, correlations, and trend analysis.
"""

from pydantic import BaseModel, Field


class StatisticalTest(BaseModel):
    """Pydantic model representing general statistical test metrics."""

    analysis_type: str = Field(..., description="E.g., Chi-Square, ANOVA, T-Test.")
    target_columns: list[str] = Field(..., description="Columns tested during the calculation.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Inferred confidence level.")
    significance: float = Field(..., ge=0.0, le=1.0, description="P-value of the test.")
    evidence: str = Field(..., description="Details of critical stats (e.g. F-statistic, degrees of freedom).")
    interpretation: str = Field(..., description="Plain-language analysis of results.")


class CorrelationResult(BaseModel):
    """Pydantic model representing Pearson correlation metrics between two numeric variables."""

    analysis_type: str = Field("Correlation", description="Type of correlation mapping (e.g. Pearson, Spearman).")
    target_columns: list[str] = Field(..., description="The two numeric variables compared.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Estimated confidence score.")
    significance: float = Field(..., ge=0.0, le=1.0, description="Correlation p-value.")
    evidence: str = Field(..., description="Sample count and covariance support context.")
    interpretation: str = Field(..., description="Qualitative relationship description (e.g. Strong positive correlation).")
    correlation_coefficient: float = Field(..., ge=-1.0, le=1.0, description="Calculated r-value.")


class TrendAnalysis(BaseModel):
    """Pydantic model representing linear regression or temporal sequence properties."""

    analysis_type: str = Field(..., description="E.g., Simple Linear Regression, Moving Average.")
    target_columns: list[str] = Field(..., description="Variables mapped, usually time sequence X and target Y.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analytical confidence of the model.")
    significance: float = Field(..., ge=0.0, le=1.0, description="Model fit p-value.")
    evidence: str = Field(..., description="Regression equation details and change point alerts.")
    interpretation: str = Field(..., description="Summary trend interpretation.")
    slope: float = Field(..., description="Slope of regression line (m in mx + c).")
    intercept: float = Field(..., description="Intercept of regression line (c in mx + c).")
    r_squared: float = Field(..., ge=0.0, le=1.0, description="Coeff of determination.")


class StatisticalSummary(BaseModel):
    """Consolidated summary model containing all parsed statistical calculations."""

    tests: list[StatisticalTest] = Field(default_factory=list)
    correlations: list[CorrelationResult] = Field(default_factory=list)
    trends: list[TrendAnalysis] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

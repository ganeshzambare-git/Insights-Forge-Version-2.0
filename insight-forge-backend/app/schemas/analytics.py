"""
Insight Forge V2 — Analytics Schemas.

Defines Pydantic schemas for analytics API requests and responses.
"""

from pydantic import BaseModel


class AnalyticsRequest(BaseModel):
    """Incoming request model for triggering analytics pipeline runs."""
    pass


class AnalyticsResponse(BaseModel):
    """Outgoing response schema containing analytics run summaries."""
    pass

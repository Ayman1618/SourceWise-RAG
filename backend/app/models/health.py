"""Health check response models."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check status response payload."""

    status: str = Field(default="ok", description="Operational status of the backend API")

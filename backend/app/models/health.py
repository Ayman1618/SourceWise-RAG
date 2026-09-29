"""Health and readiness check response models."""

from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check status response payload (liveness)."""

    status: str = Field(default="ok", description="Operational status of the backend API")


class ReadinessResponse(BaseModel):
    """Readiness check response payload."""

    status: str = Field(default="ready", description="Readiness status of the backend service")
    database: str = Field(default="connected", description="Vector database connectivity status")
    details: dict[str, Any] | None = Field(default=None, description="Component status details")


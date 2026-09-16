"""Health check endpoint router."""

from fastapi import APIRouter
from app.models.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the operational status of the API without external dependencies.",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse(status="ok")

"""Health and readiness check endpoint router."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_vector_store_service
from app.models.health import HealthResponse, ReadinessResponse
from app.services.vector_store import BaseVectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check (Liveness)",
    description="Returns the operational status of the API without external dependencies.",
)
async def health_check() -> HealthResponse:
    """Return application liveness status without external dependency checks."""
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Verifies essential service dependencies (vector store connectivity) for traffic readiness.",
    responses={
        200: {"description": "Service is ready to accept traffic", "model": ReadinessResponse},
        503: {"description": "Service dependencies are not ready", "model": ReadinessResponse},
    },
)
async def readiness_check(
    vector_store: BaseVectorStoreService = Depends(get_vector_store_service),
) -> ReadinessResponse:
    """Check readiness by verifying vector store connectivity."""
    try:
        is_connected = vector_store.collection_exists()
        return ReadinessResponse(
            status="ready",
            database="connected",
            details={"collection_checked": True, "collection_exists": is_connected},
        )
    except Exception as exc:
        logger.warning("Readiness check failed on vector store dependency: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database dependency is currently unreachable.",
        ) from exc


"""Dependency injection providers for FastAPI routes."""

from fastapi import Depends

from app.services.generation import BaseGenerationService, GroundedGenerationService
from app.services.query import (
    BaseQueryOrchestrationService,
    QueryOrchestrationService,
)
from app.services.retrieval import BaseRetrievalService, QdrantRetrievalService


def get_retrieval_service() -> BaseRetrievalService:
    """Provide the default semantic retrieval service."""
    return QdrantRetrievalService()


def get_generation_service() -> BaseGenerationService:
    """Provide the default grounded answer generation service."""
    return GroundedGenerationService()


def get_query_orchestration_service(
    retrieval_service: BaseRetrievalService = Depends(get_retrieval_service),
    generation_service: BaseGenerationService = Depends(get_generation_service),
) -> BaseQueryOrchestrationService:
    """Provide the application query orchestration service wired with its dependencies."""
    return QueryOrchestrationService(
        retrieval_service=retrieval_service,
        generation_service=generation_service,
    )

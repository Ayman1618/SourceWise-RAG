"""FastAPI router for RAG query execution (POST /api/v1/query)."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_query_orchestration_service
from app.models.generation import Answer
from app.models.query import QueryRequest
from app.services.query import BaseQueryOrchestrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post(
    "/query",
    response_model=Answer,
    status_code=status.HTTP_200_OK,
    summary="Execute grounded enterprise RAG query",
    description=(
        "Processes a natural language question through semantic retrieval and grounded answer generation.\n\n"
        "**Pipeline Workflow:**\n"
        "1. **Validation**: Validates question length, non-empty content, and retrieval parameters.\n"
        "2. **Semantic Retrieval**: Retrieves top-k evidence chunks from vector storage matching query embeddings and optional metadata filters.\n"
        "3. **Grounded Generation**: Synthesizes a factual answer strictly supported by retrieved evidence with verifiable citations.\n"
        "4. **Sufficiency & Refusal**: Classifies evidence status (`sufficient`, `insufficient`, `refused`). If evidence is missing or unverified, a safe refusal message is returned."
    ),
    responses={
        200: {
            "description": "Successfully answered query with evidence status and citations.",
            "model": Answer,
        },
        400: {
            "description": "Invalid query parameter or blank query string.",
        },
        422: {
            "description": "Request validation failure (e.g. invalid type or query exceeding maximum length).",
        },
        500: {
            "description": "Internal server error occurred during retrieval or generation.",
        },
    },
)
async def execute_query(
    payload: QueryRequest,
    query_service: BaseQueryOrchestrationService = Depends(get_query_orchestration_service),
) -> Answer:
    """Execute end-to-end query orchestration pipeline and return grounded Answer."""
    try:
        answer = await query_service.query(
            query=payload,
            top_k=payload.top_k,
            filters=payload.filters,
        )
        return answer
    except ValueError as exc:
        logger.warning("Invalid query request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected failure during query orchestration: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the query. Please try again later.",
        ) from exc

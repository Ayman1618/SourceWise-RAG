"""FastAPI router for RAG query execution (POST /api/v1/query)."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.generation import Answer
from app.services.generation import GroundedGenerationService
from app.services.retrieval import MockRetrievalService

router = APIRouter(prefix="/api/v1", tags=["query"])


class QueryPayload(BaseModel):
    """Request payload for RAG query endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        description="User question to query against internal knowledge base",
        examples=["How do I troubleshoot repeated login failures?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of evidence chunks to retrieve",
    )


@router.post("/query", response_model=Answer, status_code=status.HTTP_200_OK)
async def execute_rag_query(payload: QueryPayload) -> Answer:
    """Execute RAG query against internal document index and return grounded Answer.

    Contract:
    Request: POST /api/v1/query Payload: { "query": "..." }
    Response: Answer model containing query, answer, citations, evidence, evidence_status, has_sufficient_evidence.
    """
    cleaned_query = payload.query.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty or whitespace only",
        )

    try:
        retrieval_service = MockRetrievalService()
        generation_service = GroundedGenerationService()

        retrieved_result = await retrieval_service.retrieve(
            cleaned_query, top_k=payload.top_k
        )
        answer = await generation_service.generate(
            cleaned_query, retrieved_result.retrieved_chunks
        )
        return answer
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the RAG query: {str(exc)}",
        ) from exc

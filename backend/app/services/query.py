"""Application-level query orchestration service for SourceWise RAG."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.models.generation import Answer
from app.models.query import QueryRequest
from app.models.retrieval import RetrievalQuery
from app.services.generation import BaseGenerationService, GroundedGenerationService
from app.services.retrieval import BaseRetrievalService, QdrantRetrievalService

logger = logging.getLogger(__name__)


class BaseQueryOrchestrationService(ABC):
    """Abstract interface for end-to-end RAG query orchestration."""

    @abstractmethod
    async def query(
        self,
        query: str | QueryRequest | RetrievalQuery,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Answer:
        """Execute end-to-end query workflow: retrieval -> generation -> grounded answer.

        Args:
            query: User question string or structured QueryRequest / RetrievalQuery.
            top_k: Maximum number of evidence chunks to retrieve.
            filters: Optional metadata filtering criteria.
            **kwargs: Additional parameters forwarded to retrieval and generation.

        Returns:
            Answer: Grounded answer with citations, evidence, and evidence sufficiency status.
        """
        raise NotImplementedError


class QueryOrchestrationService(BaseQueryOrchestrationService):
    """Coordinates retrieval and grounded generation to produce verifiable answers.

    Pipeline:
    User Query (QueryRequest / string)
        ↓
    RetrievalService (QdrantRetrievalService)
        ↓
    RetrievedChunk[]
        ↓
    GenerationService (GroundedGenerationService)
        ↓
    Answer (Validated Answer + Citations)
    """

    def __init__(
        self,
        retrieval_service: BaseRetrievalService | None = None,
        generation_service: BaseGenerationService | None = None,
    ) -> None:
        """Initialize the orchestration service with retrieval and generation dependencies.

        Args:
            retrieval_service: Service responsible for semantic evidence retrieval.
            generation_service: Service responsible for grounded answer generation.
        """
        self.retrieval_service = retrieval_service or QdrantRetrievalService()
        self.generation_service = generation_service or GroundedGenerationService()

    def _extract_params(
        self,
        query: str | QueryRequest | RetrievalQuery,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> tuple[str, int, dict[str, Any] | None]:
        """Extract and validate query parameters."""
        if isinstance(query, QueryRequest):
            query_text = query.query
            effective_top_k = query.top_k if top_k == 5 and query.top_k != 5 else top_k
            effective_filters = filters if filters is not None else query.filters
        elif isinstance(query, RetrievalQuery):
            query_text = query.query
            effective_top_k = query.top_k if top_k == 5 and query.top_k != 5 else top_k
            effective_filters = filters if filters is not None else query.filters
        elif isinstance(query, str):
            query_text = query
            effective_top_k = top_k
            effective_filters = filters
        else:
            raise ValueError(f"Unsupported query type: {type(query)}")

        if not query_text or not query_text.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        cleaned_query = query_text.strip()
        return cleaned_query, effective_top_k, effective_filters

    async def query(
        self,
        query: str | QueryRequest | RetrievalQuery,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Answer:
        """Execute end-to-end RAG workflow.

        Args:
            query: User question string or QueryRequest instance.
            top_k: Maximum number of evidence chunks to retrieve.
            filters: Optional metadata filtering criteria.
            **kwargs: Extra parameters passed down to retrieval or generation.

        Returns:
            Answer: Grounded response model containing answer, citations, evidence, and status.

        Raises:
            ValueError: If the query is empty or invalid.
            Exception: If underlying retrieval or generation fails.
        """
        query_text, effective_top_k, effective_filters = self._extract_params(
            query=query, top_k=top_k, filters=filters
        )

        logger.info(
            "Orchestrating query execution: query_length=%d, top_k=%d, has_filters=%s",
            len(query_text),
            effective_top_k,
            effective_filters is not None,
        )

        # 1. Evidence Retrieval
        retrieved_chunks = await self.retrieval_service.retrieve(
            query=query_text,
            top_k=effective_top_k,
            filters=effective_filters,
            **kwargs,
        )

        logger.info(
            "Retrieved %d evidence chunks for query",
            len(retrieved_chunks),
        )

        # 2. Grounded Generation
        answer = await self.generation_service.generate(
            query=query_text,
            evidence=retrieved_chunks,
            **kwargs,
        )

        logger.info(
            "Generated answer for query with status=%s, citations=%d",
            answer.evidence_status.value,
            len(answer.citations),
        )

        return answer

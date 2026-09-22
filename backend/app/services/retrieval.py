"""Pipeline interface and implementation for evidence retrieval services."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.retrieval import RetrievalQuery, RetrievedChunk
from app.services.embedding import BaseEmbeddingService, OpenAIEmbeddingService
from app.services.vector_store import BaseVectorStoreService, QdrantVectorStoreService


class BaseRetrievalService(ABC):
    """Abstract contract for semantic, keyword, and hybrid evidence retrieval."""

    @abstractmethod
    async def retrieve(
        self,
        query: str | RetrievalQuery,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant evidence chunks for a given search query.

        Args:
            query: Search query string or structured RetrievalQuery instance.
            top_k: Maximum number of relevant chunks to return.
            filters: Optional metadata filtering criteria.
            **kwargs: Additional retrieval options (e.g. score threshold, reranker config).

        Returns:
            list[RetrievedChunk]: Ordered list of scored and ranked evidence chunks.
        """
        raise NotImplementedError


class QdrantRetrievalService(BaseRetrievalService):
    """Semantic retrieval service using vector embeddings and vector store abstraction."""

    MAX_TOP_K: int = 100

    def __init__(
        self,
        embedding_service: BaseEmbeddingService | None = None,
        vector_store_service: BaseVectorStoreService | None = None,
    ) -> None:
        """Initialize the Qdrant retrieval service via dependency injection.

        Args:
            embedding_service: Embedding generation service (defaults to OpenAIEmbeddingService()).
            vector_store_service: Vector store service (defaults to QdrantVectorStoreService()).
        """
        self.embedding_service = embedding_service or OpenAIEmbeddingService()
        self.vector_store_service = vector_store_service or QdrantVectorStoreService()

    def _extract_query_and_params(
        self,
        query: str | RetrievalQuery,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> tuple[str, int, dict[str, Any] | None]:
        """Extract and validate query parameters."""
        if isinstance(query, RetrievalQuery):
            query_text = query.query
            effective_filters = filters if filters is not None else query.filters
            effective_top_k = query.top_k if top_k == 5 and query.top_k != 5 else top_k
        elif isinstance(query, str):
            query_text = query
            effective_filters = filters
            effective_top_k = top_k
        else:
            raise ValueError(f"Unsupported query type: {type(query)}")

        if not query_text or not query_text.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        if not isinstance(effective_top_k, int) or effective_top_k < 1 or effective_top_k > self.MAX_TOP_K:
            raise ValueError(
                f"top_k must be an integer between 1 and {self.MAX_TOP_K}, got {effective_top_k}"
            )

        return query_text, effective_top_k, effective_filters

    async def retrieve(
        self,
        query: str | RetrievalQuery,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
        **kwargs: Any,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant evidence chunks for a given search query.

        Retrieval flow:
        1. Validate query string or RetrievalQuery object and top_k.
        2. Generate dense query embedding vector via embedding_service.
        3. Search vector store via vector_store_service.search().
        4. Reconstruct RetrievedChunk instances with 1-indexed ranks and preserved provenance.

        Args:
            query: Query text string or RetrievalQuery instance.
            top_k: Maximum number of chunks to return (1 <= top_k <= 100, default: 5).
            filters: Optional metadata filtering criteria (e.g. product, department, document_id).
            score_threshold: Optional minimum similarity score threshold.
            **kwargs: Additional search arguments forwarded to vector store.

        Returns:
            list[RetrievedChunk]: Ordered list of ranked retrieved chunks.

        Raises:
            ValueError: If query is empty/whitespace or top_k is outside valid bounds.
        """
        query_text, effective_top_k, effective_filters = self._extract_query_and_params(
            query=query, top_k=top_k, filters=filters
        )

        # Generate query embedding
        query_vector = self.embedding_service.query_embedding(query_text)

        # Search vector store via vector store abstraction
        search_results = self.vector_store_service.search(
            vector=query_vector,
            top_k=effective_top_k,
            filters=effective_filters,
            score_threshold=score_threshold,
            **kwargs,
        )

        # Convert to RetrievedChunk instances with 1-indexed rank
        retrieved_chunks: list[RetrievedChunk] = []
        for rank, res in enumerate(search_results, start=1):
            retrieved_chunks.append(
                RetrievedChunk(
                    chunk=res.chunk,
                    score=res.score,
                    rank=rank,
                    retrieval_method="dense",
                )
            )

        return retrieved_chunks

"""Pipeline interface for evidence retrieval services."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.retrieval import RetrievalQuery, RetrievedChunk


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

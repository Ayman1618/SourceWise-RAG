"""Embedding service interface and OpenAI-compatible implementation."""

from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from app.core.config import settings


class BaseEmbeddingService(ABC):
    """Abstract contract for text embedding generation services."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for a single text string.

        Args:
            text: Input text string to embed.

        Returns:
            list[float]: Vector embedding representation of the input text.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for a list of text strings.

        Args:
            texts: List of text strings to embed.

        Returns:
            list[list[float]]: Ordered list of vector embeddings corresponding to inputs.
        """
        raise NotImplementedError

    @abstractmethod
    def query_embedding(self, query: str) -> list[float]:
        """Generate an embedding vector for a search query.

        Args:
            query: Search query text to embed.

        Returns:
            list[float]: Query vector embedding representation.
        """
        raise NotImplementedError


class OpenAIEmbeddingService(BaseEmbeddingService):
    """Embedding service using an OpenAI-compatible API endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        batch_size: int | None = None,
        client: OpenAI | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the OpenAI-compatible embedding service.

        Args:
            api_key: API key for the embedding provider (defaults to settings.embedding_api_key).
            model: Embedding model name (defaults to settings.embedding_model).
            base_url: Base URL for OpenAI-compatible API (defaults to settings.embedding_base_url).
            batch_size: Number of texts per batch request (defaults to settings.embedding_batch_size).
            client: Optional pre-configured OpenAI client instance (useful for testing/mocking).
            **kwargs: Additional parameters passed to the OpenAI client.
        """
        self.model = model or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size or 64
        self._api_key = api_key or settings.embedding_api_key
        self._base_url = base_url or settings.embedding_base_url

        if client is not None:
            self.client = client
        else:
            # Fallback to a placeholder key if none provided to allow client initialization in test/mock mode
            effective_key = self._api_key or "mock-key-not-set"
            self.client = OpenAI(
                api_key=effective_key,
                base_url=self._base_url,
                **kwargs,
            )

    def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for a single text string.

        Args:
            text: Input text string to embed.

        Returns:
            list[float]: Vector embedding representation.

        Raises:
            ValueError: If text is empty or whitespace only.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")

        response = self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        return response.data[0].embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for a list of text strings with batching.

        Args:
            texts: List of text strings to embed.

        Returns:
            list[list[float]]: Ordered list of vector embeddings.

        Raises:
            ValueError: If texts list is empty or any item is empty/whitespace only.
        """
        if not texts:
            return []

        for idx, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {idx} cannot be empty or whitespace only")

        embeddings: list[list[float]] = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self.model,
            )
            # Ensure order is preserved matching response data index
            batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
            embeddings.extend(batch_embeddings)

        return embeddings

    def query_embedding(self, query: str) -> list[float]:
        """Generate an embedding vector for a search query.

        Args:
            query: Search query text to embed.

        Returns:
            list[float]: Query vector embedding representation.

        Raises:
            ValueError: If query is empty or whitespace only.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        return self.embed_text(query)

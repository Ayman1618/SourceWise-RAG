"""Embedding service interface and Google Gemini / OpenAI-compatible implementations."""

from abc import ABC, abstractmethod
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings

try:
    from openai import OpenAI
except ImportError:
    OpenAI = Any  # type: ignore[misc,assignment]


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


class GeminiEmbeddingService(BaseEmbeddingService):
    """Embedding service using Google Gemini's embedding API (free-tier compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
        batch_size: int | None = None,
        client: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Google Gemini embedding service.

        Args:
            api_key: API key for Google Gemini (defaults to settings.gemini_api_key / settings.embedding_api_key).
            model: Embedding model name (defaults to settings.gemini_embedding_model or settings.embedding_model).
            dimension: Output vector dimensionality (defaults to settings.gemini_embedding_dimension or 1536).
            batch_size: Number of texts per batch request (defaults to settings.embedding_batch_size).
            client: Optional pre-configured genai.Client instance (useful for testing/mocking).
            **kwargs: Additional parameters passed to the genai.Client.
        """
        self.model = model or settings.gemini_embedding_model or settings.embedding_model
        self.dimension = (
            dimension
            if dimension is not None
            else (settings.gemini_embedding_dimension or settings.embedding_dimension or 1536)
        )
        self.batch_size = batch_size or settings.embedding_batch_size or 64
        self._api_key = api_key or settings.gemini_api_key or settings.embedding_api_key

        if client is not None:
            self.client = client
        else:
            effective_key = self._api_key or "mock-key-not-set"
            self.client = genai.Client(
                api_key=effective_key,
                **kwargs,
            )

    def _get_embed_config(self) -> types.EmbedContentConfig | None:
        """Construct the EmbedContentConfig with configured output dimensionality."""
        if self.dimension is not None:
            return types.EmbedContentConfig(output_dimensionality=self.dimension)
        return None

    def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for a single text string.

        Args:
            text: Input text string to embed.

        Returns:
            list[float]: Dense vector embedding representation.

        Raises:
            ValueError: If text is empty or whitespace only, or API returns no embeddings.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")

        config = self._get_embed_config()
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=config,
        )

        if not response or not hasattr(response, "embeddings") or not response.embeddings:
            raise ValueError("No embeddings returned by Gemini embedding API")

        return list(response.embeddings[0].values)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for a list of text strings with batching.

        Args:
            texts: List of text strings to embed.

        Returns:
            list[list[float]]: Ordered list of vector embeddings.

        Raises:
            ValueError: If texts list is invalid, item is empty/whitespace, or API count mismatches.
        """
        if not texts:
            return []

        for idx, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {idx} cannot be empty or whitespace only")

        embeddings: list[list[float]] = []
        config = self._get_embed_config()

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            response = self.client.models.embed_content(
                model=self.model,
                contents=batch,
                config=config,
            )

            if (
                not response
                or not hasattr(response, "embeddings")
                or not response.embeddings
                or len(response.embeddings) != len(batch)
            ):
                returned_count = len(response.embeddings) if response and hasattr(response, "embeddings") and response.embeddings else 0
                raise ValueError(
                    f"Embedding count mismatch from Gemini API: expected {len(batch)}, got {returned_count}"
                )

            batch_embeddings = [list(item.values) for item in response.embeddings]
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


class OpenAIEmbeddingService(BaseEmbeddingService):
    """Optional embedding service using an OpenAI-compatible API endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        batch_size: int | None = None,
        client: Any | None = None,
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
            try:
                from openai import OpenAI as OpenAIClient
            except ImportError as exc:
                raise ImportError(
                    "openai package is not installed. Install openai or use GeminiEmbeddingService."
                ) from exc

            effective_key = self._api_key or "mock-key-not-set"
            self.client = OpenAIClient(
                api_key=effective_key,
                base_url=self._base_url,
                **kwargs,
            )

    def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for a single text string."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")

        response = self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        return response.data[0].embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for a list of text strings with batching."""
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
            batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
            embeddings.extend(batch_embeddings)

        return embeddings

    def query_embedding(self, query: str) -> list[float]:
        """Generate an embedding vector for a search query."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        return self.embed_text(query)


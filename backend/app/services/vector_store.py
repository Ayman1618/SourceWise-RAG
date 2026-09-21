"""Vector store service interface and Qdrant implementation."""

import uuid
from abc import ABC, abstractmethod
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.models.chunk import Chunk


class BaseVectorStoreService(ABC):
    """Abstract contract for vector database storage and collection management."""

    @abstractmethod
    def connect(self) -> Any:
        """Establish or verify connection to the vector store."""
        raise NotImplementedError

    @abstractmethod
    def collection_exists(self, collection_name: str | None = None) -> bool:
        """Check if a vector collection exists.

        Args:
            collection_name: Name of the collection (defaults to configured collection).

        Returns:
            bool: True if collection exists, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def create_collection_if_not_exists(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        distance: str | None = None,
    ) -> bool:
        """Create a collection if it does not already exist.

        Args:
            collection_name: Name of the collection to create.
            vector_size: Dimensionality of vectors in the collection.
            distance: Distance metric (e.g. 'Cosine', 'Dot', 'Euclid').

        Returns:
            bool: True if collection was created, False if it already existed.
        """
        raise NotImplementedError

    @abstractmethod
    def store_chunks(
        self,
        chunks: list[Chunk],
        vectors: list[list[float]],
        collection_name: str | None = None,
    ) -> list[str]:
        """Store chunk vectors along with provenance metadata.

        Preserves: chunk_id -> document_id -> source metadata.

        Args:
            chunks: List of Chunk model instances.
            vectors: List of corresponding embedding vectors.
            collection_name: Target collection name (defaults to configured collection).

        Returns:
            list[str]: List of stored point IDs.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close vector store client connection and release resources."""
        raise NotImplementedError


class QdrantVectorStoreService(BaseVectorStoreService):
    """Qdrant vector store service implementation for chunk embedding storage."""

    _DISTANCE_MAP = {
        "cosine": Distance.COSINE,
        "dot": Distance.DOT,
        "euclid": Distance.EUCLID,
    }

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        vector_size: int | None = None,
        distance: str | None = None,
        timeout: float | None = None,
        client: QdrantClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Qdrant vector store service.

        Args:
            url: Qdrant endpoint URL (defaults to settings.qdrant_url).
            api_key: Qdrant API key (defaults to settings.qdrant_api_key).
            collection_name: Default collection name (defaults to settings.qdrant_collection_name).
            vector_size: Default vector dimension (defaults to settings.qdrant_vector_size).
            distance: Distance metric (defaults to settings.qdrant_distance).
            timeout: Connection timeout in seconds (defaults to settings.qdrant_timeout).
            client: Optional pre-configured QdrantClient (useful for testing/mocking).
            **kwargs: Additional parameters passed to QdrantClient.
        """
        self.url = url or settings.qdrant_url
        self.api_key = api_key or settings.qdrant_api_key
        self.collection_name = collection_name or settings.qdrant_collection_name
        self.vector_size = vector_size or settings.qdrant_vector_size
        self.distance_str = distance or settings.qdrant_distance
        self.timeout = timeout or settings.qdrant_timeout

        if client is not None:
            self._client = client
        else:
            self._client = None
            self._client_kwargs = kwargs

    @property
    def client(self) -> QdrantClient:
        """Get or initialize the underlying QdrantClient instance."""
        if self._client is None:
            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=self.timeout,
                **getattr(self, "_client_kwargs", {}),
            )
        return self._client

    def connect(self) -> QdrantClient:
        """Verify or establish connection to Qdrant."""
        return self.client

    def _resolve_distance(self, distance_str: str | None) -> Distance:
        """Resolve distance string to Qdrant Distance enum."""
        dist = (distance_str or self.distance_str).lower()
        if dist not in self._DISTANCE_MAP:
            valid_keys = ", ".join(self._DISTANCE_MAP.keys())
            raise ValueError(f"Unsupported distance metric '{distance_str}'. Valid metrics: {valid_keys}")
        return self._DISTANCE_MAP[dist]

    @staticmethod
    def chunk_id_to_point_id(chunk_id: str) -> str:
        """Generate a deterministic UUID string from a chunk identifier.

        Ensures idempotent upserts where re-indexing a chunk updates the same point.

        Args:
            chunk_id: Unique string chunk identifier.

        Returns:
            str: Deterministic UUIDv5 string representation.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def collection_exists(self, collection_name: str | None = None) -> bool:
        """Check if a vector collection exists in Qdrant.

        Args:
            collection_name: Target collection name (defaults to self.collection_name).

        Returns:
            bool: True if collection exists, False otherwise.
        """
        name = collection_name or self.collection_name
        return bool(self.client.collection_exists(collection_name=name))

    def create_collection_if_not_exists(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        distance: str | None = None,
    ) -> bool:
        """Create a collection if it does not already exist.

        Args:
            collection_name: Name of the collection to create.
            vector_size: Dimensionality of vectors (defaults to self.vector_size).
            distance: Distance metric string (defaults to self.distance_str).

        Returns:
            bool: True if collection was created, False if it already existed.
        """
        name = collection_name or self.collection_name
        if self.collection_exists(name):
            return False

        effective_size = vector_size or self.vector_size
        effective_distance = self._resolve_distance(distance)

        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=effective_size,
                distance=effective_distance,
            ),
        )
        return True

    def build_payload(self, chunk: Chunk) -> dict[str, Any]:
        """Construct the vector payload preserving citation provenance.

        Payload schema:
            chunk_id: str
            document_id: str
            text: str
            chunk_index: int
            token_count: int | None
            metadata: dict[str, Any] (contains document title, source, filepath, etc.)

        Args:
            chunk: Input Chunk instance.

        Returns:
            dict[str, Any]: Structured dictionary payload.
        """
        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "chunk_index": chunk.chunk_index,
            "token_count": chunk.token_count,
            "metadata": chunk.metadata,
        }

    def store_chunks(
        self,
        chunks: list[Chunk],
        vectors: list[list[float]],
        collection_name: str | None = None,
    ) -> list[str]:
        """Store chunk vectors and provenance metadata in Qdrant.

        Preserves: chunk_id -> document_id -> source metadata.

        Args:
            chunks: List of Chunk model instances to store.
            vectors: List of corresponding embedding vectors.
            collection_name: Target collection name (defaults to self.collection_name).

        Returns:
            list[str]: List of stored point IDs (deterministic UUIDs).

        Raises:
            ValueError: If number of chunks does not match number of vectors.
        """
        if not chunks and not vectors:
            return []

        if len(chunks) != len(vectors):
            raise ValueError(
                f"Mismatch between number of chunks ({len(chunks)}) and vectors ({len(vectors)})"
            )

        name = collection_name or self.collection_name

        # Ensure collection exists; infer vector_size from first vector if available
        first_vec_len = len(vectors[0]) if vectors and len(vectors[0]) > 0 else self.vector_size
        self.create_collection_if_not_exists(
            collection_name=name,
            vector_size=first_vec_len,
        )

        points: list[PointStruct] = []
        point_ids: list[str] = []

        for chunk, vector in zip(chunks, vectors, strict=True):
            if not vector:
                raise ValueError(f"Vector for chunk '{chunk.chunk_id}' is empty")

            point_id = self.chunk_id_to_point_id(chunk.chunk_id)
            payload = self.build_payload(chunk)

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
            points.append(point)
            point_ids.append(point_id)

        self.client.upsert(
            collection_name=name,
            points=points,
        )

        return point_ids

    def close(self) -> None:
        """Close the Qdrant client connection."""
        if self._client is not None:
            self.client.close()
            self._client = None

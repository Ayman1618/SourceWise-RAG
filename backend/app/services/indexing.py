"""Document and chunk indexing pipeline service for SourceWise RAG."""

from __future__ import annotations

from abc import ABC, abstractmethod
import inspect
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunking import ChunkingService
from app.services.embedding import BaseEmbeddingService, OpenAIEmbeddingService
from app.services.ingestion import BaseIngestionService, DocumentIngestionService
from app.services.vector_store import BaseVectorStoreService, QdrantVectorStoreService


class IndexingError(Exception):
    """Raised when document or chunk indexing encounters an unrecoverable failure."""


class BaseIndexingService(ABC):
    """Abstract contract for document and chunk indexing services."""

    @abstractmethod
    async def index_documents(
        self,
        documents: list[Document] | Document,
        **kwargs: Any,
    ) -> list[str]:
        """Index one or more normalized documents into the vector store.

        Segments documents into traceable chunks, generates dense embeddings in
        batches, ensures vector collection creation, and stores points with complete
        citation provenance.

        Args:
            documents: Normalized Document instance or list of Document instances.
            **kwargs: Additional indexing configurations (e.g. collection_name, batch_size).

        Returns:
            list[str]: Stored point IDs.
        """
        raise NotImplementedError

    @abstractmethod
    async def index_chunks(
        self,
        chunks: list[Chunk],
        **kwargs: Any,
    ) -> list[str]:
        """Index a list of pre-extracted chunks into the vector store.

        Generates dense embeddings in batches, ensures vector collection creation,
        and stores points with complete citation provenance.

        Args:
            chunks: List of Chunk instances to embed and store.
            **kwargs: Additional indexing configurations (e.g. collection_name, batch_size).

        Returns:
            list[str]: Stored point IDs.
        """
        raise NotImplementedError


class DocumentIndexingService(BaseIndexingService):
    """Production indexing service connecting ingestion/chunking to vector store.

    Adheres to:
    - Loose coupling via BaseEmbeddingService and BaseVectorStoreService abstractions.
    - Batch embedding to minimize API latency and payload overhead.
    - Idempotent point indexing via deterministic UUIDs preserving provenance.
    - Full metadata preservation across document, chunk, and vector layers.
    """

    def __init__(
        self,
        embedding_service: BaseEmbeddingService | None = None,
        vector_store_service: BaseVectorStoreService | None = None,
        chunking_service: BaseIngestionService | ChunkingService | None = None,
        batch_size: int | None = None,
    ) -> None:
        """Initialize DocumentIndexingService with required abstractions.

        Args:
            embedding_service: Text embedding service (defaults to OpenAIEmbeddingService()).
            vector_store_service: Vector store service (defaults to QdrantVectorStoreService()).
            chunking_service: Chunking/ingestion service (defaults to DocumentIngestionService()).
            batch_size: Default batch size for embedding and upsert operations.
        """
        self.embedding_service = embedding_service or OpenAIEmbeddingService()
        self.vector_store_service = vector_store_service or QdrantVectorStoreService()
        self.chunking_service = chunking_service or DocumentIngestionService()
        self.batch_size = batch_size

    async def _chunk_document(self, document: Document, **kwargs: Any) -> list[Chunk]:
        """Chunk a document using either sync or async chunking services."""
        chunk_func = getattr(self.chunking_service, "chunk_document", None)
        if not callable(chunk_func):
            raise TypeError(
                f"Configured chunking_service '{type(self.chunking_service)}' has no callable 'chunk_document'"
            )

        result = chunk_func(document, **kwargs)
        if inspect.iscoroutine(result):
            return await result
        return result

    async def index_documents(
        self,
        documents: list[Document] | Document,
        collection_name: str | None = None,
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Index one or more normalized documents into the vector store.

        Workflow:
        1. Receive normalized Document instances.
        2. Segment documents into traceable Chunks via the chunking service.
        3. Delegate chunks to index_chunks for batch embedding and vector upsert.

        Args:
            documents: Normalized Document instance or list of Document instances.
            collection_name: Target vector collection name.
            batch_size: Batch size override for embedding and upsert.
            **kwargs: Additional parameters forwarded to chunker or vector store.

        Returns:
            list[str]: Stored point IDs.
        """
        if not documents:
            return []

        doc_list = [documents] if isinstance(documents, Document) else list(documents)
        if not doc_list:
            return []

        all_chunks: list[Chunk] = []
        for doc in doc_list:
            if not isinstance(doc, Document):
                raise TypeError(f"Expected Document instance, got {type(doc).__name__}")
            chunks = await self._chunk_document(doc, **kwargs)
            if chunks:
                all_chunks.extend(chunks)

        if not all_chunks:
            return []

        return await self.index_chunks(
            chunks=all_chunks,
            collection_name=collection_name,
            batch_size=batch_size,
            **kwargs,
        )

    async def index_chunks(
        self,
        chunks: list[Chunk],
        collection_name: str | None = None,
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Index pre-segmented chunks directly into the vector store.

        Workflow:
        1. Validate chunk list and batch configuration.
        2. For each batch, generate dense vector embeddings via BaseEmbeddingService.embed_texts.
        3. Validate embedding count parity with chunk count.
        4. Ensure vector collection exists.
        5. Persist vectors and metadata in vector store via BaseVectorStoreService.store_chunks.

        Args:
            chunks: List of Chunk instances to embed and index.
            collection_name: Target vector collection name.
            batch_size: Batch size override for embedding generation and storage.
            **kwargs: Additional parameters forwarded to embedding or vector store.

        Returns:
            list[str]: List of stored point IDs.

        Raises:
            ValueError: If batch_size <= 0 or if embedding count does not match chunk count.
            IndexingError: If embedding generation or vector store upsert fails.
        """
        if not chunks:
            return []

        eff_batch_size = (
            batch_size
            if batch_size is not None
            else (
                self.batch_size
                if self.batch_size is not None
                else getattr(settings, "embedding_batch_size", 64)
            )
        )
        if eff_batch_size <= 0:
            raise ValueError(f"batch_size must be a positive integer, got {eff_batch_size}")

        all_point_ids: list[str] = []

        # Process chunks in batches
        for i in range(0, len(chunks), eff_batch_size):
            batch_chunks = chunks[i : i + eff_batch_size]
            texts = [c.text for c in batch_chunks]

            # 1. Generate embeddings in batch
            try:
                vectors = self.embedding_service.embed_texts(texts)
            except Exception as exc:
                if isinstance(exc, (ValueError, IndexingError)):
                    raise
                raise IndexingError(f"Embedding generation failed: {exc}") from exc

            # 2. Parity check between chunks and vectors
            if len(vectors) != len(batch_chunks):
                raise ValueError(
                    f"Embedding count mismatch: expected {len(batch_chunks)} vectors, "
                    f"got {len(vectors)} from embedding service"
                )

            # 3. Create collection if necessary using inferred vector dimension
            if vectors and len(vectors[0]) > 0:
                try:
                    self.vector_store_service.create_collection_if_not_exists(
                        collection_name=collection_name,
                        vector_size=len(vectors[0]),
                    )
                except Exception as exc:
                    if isinstance(exc, (ValueError, IndexingError)):
                        raise
                    raise IndexingError(f"Failed to create/verify collection: {exc}") from exc

            # 4. Store chunk vectors and complete metadata in vector store
            try:
                point_ids = self.vector_store_service.store_chunks(
                    chunks=batch_chunks,
                    vectors=vectors,
                    collection_name=collection_name,
                )
            except Exception as exc:
                if isinstance(exc, (ValueError, IndexingError)):
                    raise
                raise IndexingError(f"Vector store upsert failed: {exc}") from exc

            all_point_ids.extend(point_ids)

        return all_point_ids


def run_indexing_cli(
    directory_path: str | Path | None = None,
    collection_name: str | None = None,
    batch_size: int | None = None,
    in_memory: bool = False,
    embedding_service: BaseEmbeddingService | None = None,
    vector_store_service: BaseVectorStoreService | None = None,
) -> tuple[list[Document], list[Chunk], list[str]]:
    """Synchronous CLI helper to ingest, chunk, embed, and index documents.

    Args:
        directory_path: Path to markdown documents directory (defaults to data/sample-documents).
        collection_name: Target vector collection name.
        batch_size: Batch size for embeddings and upserts.
        in_memory: If True, uses an in-memory Qdrant client and stub embeddings for offline execution.
        embedding_service: Optional custom BaseEmbeddingService.
        vector_store_service: Optional custom BaseVectorStoreService.

    Returns:
        tuple[list[Document], list[Chunk], list[str]]: Indexed documents, extracted chunks, and stored point IDs.
    """
    import asyncio
    import hashlib

    target_dir = (
        Path(directory_path)
        if directory_path
        else Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample-documents"
    )

    ingestion_service = DocumentIngestionService()

    if in_memory:
        from qdrant_client import QdrantClient

        class _OfflineStubEmbeddingService(BaseEmbeddingService):
            def embed_text(self, text: str) -> list[float]:
                h = hashlib.sha256(text.encode("utf-8")).digest()
                return [b / 255.0 for b in h[:16]]

            def embed_texts(self, texts: list[str]) -> list[list[float]]:
                return [self.embed_text(t) for t in texts]

            def query_embedding(self, query: str) -> list[float]:
                return self.embed_text(query)

        emb_service = embedding_service or _OfflineStubEmbeddingService()
        vs_service = vector_store_service or QdrantVectorStoreService(
            client=QdrantClient(":memory:"),
            collection_name=collection_name or "offline_sample_docs",
            vector_size=16,
        )
    else:
        emb_service = embedding_service or OpenAIEmbeddingService()
        vs_service = vector_store_service or QdrantVectorStoreService(
            collection_name=collection_name or settings.qdrant_collection_name,
        )

    indexing_service = DocumentIndexingService(
        embedding_service=emb_service,
        vector_store_service=vs_service,
        chunking_service=ingestion_service,
        batch_size=batch_size,
    )

    async def _execute() -> tuple[list[Document], list[Chunk], list[str]]:
        documents = await ingestion_service.ingest(target_dir)
        all_chunks: list[Chunk] = []
        for doc in documents:
            chunks = await ingestion_service.chunk_document(doc)
            all_chunks.extend(chunks)
        point_ids = await indexing_service.index_chunks(
            chunks=all_chunks,
            collection_name=collection_name,
            batch_size=batch_size,
        )
        return documents, all_chunks, point_ids

    return asyncio.run(_execute())

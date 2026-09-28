"""Document and chunk indexing pipeline service for SourceWise RAG."""

from __future__ import annotations

from abc import ABC, abstractmethod
import inspect
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.indexing import IndexingFailure, IndexingResult
from app.services.chunking import ChunkingService
from app.services.embedding import BaseEmbeddingService, OpenAIEmbeddingService
from app.services.ingestion import BaseIngestionService, DocumentIngestionService
from app.services.vector_store import BaseVectorStoreService, QdrantVectorStoreService


class IndexingError(Exception):
    """Raised when document or chunk indexing encounters an unrecoverable failure."""

    def __init__(self, message: str, result: IndexingResult | None = None) -> None:
        super().__init__(message)
        self.result = result


class BaseIndexingService(ABC):
    """Abstract contract for document and chunk indexing services."""

    @abstractmethod
    async def index_documents(
        self,
        documents: list[Document] | Document,
        **kwargs: Any,
    ) -> IndexingResult:
        """Index one or more normalized documents into the vector store.

        Segments documents into traceable chunks, generates dense embeddings in
        batches, ensures vector collection creation, and stores points with complete
        citation provenance.

        Args:
            documents: Normalized Document instance or list of Document instances.
            **kwargs: Additional indexing configurations (e.g. collection_name, batch_size).

        Returns:
            IndexingResult: Structured indexing result with metrics, point IDs, and errors.
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
    - Structured result reporting with document, chunk, point, and error metrics.
    """

    REQUIRED_METADATA_FIELDS: tuple[str, ...] = (
        "document_id",
        "chunk_id",
        "chunk_index",
        "title",
        "source_type",
        "product",
        "version",
        "department",
        "owner",
        "last_updated",
        "access_level",
        "language",
        "source_path",
    )

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

    @classmethod
    def preserve_chunk_metadata(
        cls,
        chunk: Chunk,
        document: Document | None = None,
    ) -> Chunk:
        """Ensure all 13 required metadata fields are preserved on the chunk.

        Preserves:
            document_id, chunk_id, chunk_index, title, source_type, product,
            version, department, owner, last_updated, access_level, language, source_path.
        """
        meta = dict(chunk.metadata) if chunk.metadata else {}
        meta.setdefault("document_id", chunk.document_id)
        meta.setdefault("chunk_id", chunk.chunk_id)
        meta.setdefault("chunk_index", chunk.chunk_index)

        if document is not None:
            doc_fields = {
                "title": document.title,
                "source_path": document.source_path,
                "source_type": document.source_type,
                "product": document.product,
                "version": document.version,
                "department": document.department,
                "owner": document.owner,
                "last_updated": str(document.last_updated) if document.last_updated is not None else None,
                "access_level": document.access_level,
                "language": document.language,
            }
            for k, v in doc_fields.items():
                if k not in meta or meta[k] is None:
                    meta[k] = v

        for req_field in cls.REQUIRED_METADATA_FIELDS:
            if req_field not in meta:
                meta[req_field] = getattr(chunk, req_field, None)

        chunk.metadata = meta
        return chunk

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
        raise_on_error: bool = False,
        **kwargs: Any,
    ) -> IndexingResult:
        """Index one or more normalized documents into the vector store.

        Workflow:
        1. Receive normalized Document instances.
        2. Segment documents into traceable Chunks via the chunking service.
        3. Ensure complete metadata preservation across all required provenance fields.
        4. Delegate chunks to index_chunks for batch embedding and vector upsert.
        5. Return a structured IndexingResult with counts, point IDs, and failure tracking.

        Args:
            documents: Normalized Document instance or list of Document instances.
            collection_name: Target vector collection name.
            batch_size: Batch size override for embedding and upsert.
            raise_on_error: If True, raises IndexingError on first failure instead of recording it in result.
            **kwargs: Additional parameters forwarded to chunker or vector store.

        Returns:
            IndexingResult: Structured result containing documents_processed, chunks_created,
                            chunks_indexed, point_ids, errors, and failures.
        """
        if not documents:
            return IndexingResult(
                documents_processed=0,
                chunks_created=0,
                chunks_indexed=0,
                embeddings_generated=0,
                vectors_upserted=0,
                point_ids=[],
                errors=[],
                failures=[],
            )

        doc_list = [documents] if isinstance(documents, Document) else list(documents)
        if not doc_list:
            return IndexingResult(
                documents_processed=0,
                chunks_created=0,
                chunks_indexed=0,
                embeddings_generated=0,
                vectors_upserted=0,
                point_ids=[],
                errors=[],
                failures=[],
            )

        # Validate types upfront
        for doc in doc_list:
            if not isinstance(doc, Document):
                raise TypeError(f"Expected Document instance, got {type(doc).__name__}")

        all_chunks: list[Chunk] = []
        errors: list[str] = []
        failures: list[IndexingFailure] = []
        documents_processed = 0

        for doc in doc_list:
            try:
                chunks = await self._chunk_document(doc, **kwargs)
                if chunks:
                    for c in chunks:
                        self.preserve_chunk_metadata(c, document=doc)
                    all_chunks.extend(chunks)
                documents_processed += 1
            except Exception as exc:
                err_msg = f"Failed to chunk document '{doc.document_id}': {exc}"
                failure = IndexingFailure(
                    document_id=doc.document_id,
                    stage="chunking",
                    error=err_msg,
                )
                errors.append(err_msg)
                failures.append(failure)
                if raise_on_error:
                    raise IndexingError(err_msg) from exc

        chunks_created = len(all_chunks)
        if not all_chunks:
            return IndexingResult(
                documents_processed=documents_processed,
                chunks_created=0,
                chunks_indexed=0,
                embeddings_generated=0,
                vectors_upserted=0,
                point_ids=[],
                errors=errors,
                failures=failures,
            )

        point_ids: list[str] = []
        chunks_indexed = 0
        embeddings_generated = 0
        vectors_upserted = 0
        try:
            point_ids = await self.index_chunks(
                chunks=all_chunks,
                collection_name=collection_name,
                batch_size=batch_size,
                **kwargs,
            )
            chunks_indexed = len(point_ids)
            embeddings_generated = len(all_chunks)
            vectors_upserted = len(point_ids)
        except Exception as exc:
            err_msg = f"Indexing failed during embedding or vector storage: {exc}"
            failure = IndexingFailure(
                stage="storage",
                error=err_msg,
            )
            errors.append(err_msg)
            failures.append(failure)
            if raise_on_error:
                if isinstance(exc, (ValueError, IndexingError)):
                    raise
                raise IndexingError(err_msg) from exc

        return IndexingResult(
            documents_processed=documents_processed,
            chunks_created=chunks_created,
            chunks_indexed=chunks_indexed,
            embeddings_generated=embeddings_generated,
            vectors_upserted=vectors_upserted,
            point_ids=point_ids,
            errors=errors,
            failures=failures,
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
        2. Ensure metadata preservation across all chunks.
        3. For each batch, generate dense vector embeddings via BaseEmbeddingService.embed_texts.
        4. Validate embedding count parity with chunk count.
        5. Ensure vector collection exists.
        6. Persist vectors and metadata in vector store via BaseVectorStoreService.store_chunks.

        Args:
            chunks: List of Chunk instances to embed and index.
            collection_name: Target vector collection name.
            batch_size: Batch size override for embedding generation and storage.
            **kwargs: Additional parameters forwarded to embedding or vector store.

        Returns:
            list[str]: List of stored point IDs (deterministic UUIDs).

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
            for c in batch_chunks:
                self.preserve_chunk_metadata(c)

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


def find_sample_documents_dir(custom_path: str | Path | None = None) -> Path:
    """Resolve directory containing sample documents across different invocation contexts."""
    if custom_path:
        p = Path(custom_path).resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"Specified document directory does not exist: {custom_path}")

    # Search candidate locations
    candidates = [
        # Relative to current file: backend/app/services/indexing.py -> repo root / data / sample-documents
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample-documents",
        # Relative to backend/
        Path(__file__).resolve().parent.parent.parent / "data" / "sample-documents",
        # Relative to CWD
        Path.cwd() / "data" / "sample-documents",
        Path.cwd().parent / "data" / "sample-documents",
    ]
    for cand in candidates:
        if cand.exists() and cand.is_dir():
            return cand

    return candidates[0]


class IndexingCLIResult(tuple):
    """3-tuple subclass for CLI results: (documents, chunks, point_ids) with extra metadata."""

    def __new__(
        cls,
        documents: list[Document],
        chunks: list[Chunk],
        point_ids: list[str],
        result: IndexingResult | None = None,
    ):
        return super().__new__(cls, (documents, chunks, point_ids))

    def __init__(
        self,
        documents: list[Document],
        chunks: list[Chunk],
        point_ids: list[str],
        result: IndexingResult | None = None,
    ):
        self.documents = documents
        self.chunks = chunks
        self.point_ids = point_ids
        self.result = result or IndexingResult(
            documents_processed=len(documents),
            chunks_created=len(chunks),
            chunks_indexed=len(point_ids),
            embeddings_generated=len(point_ids),
            vectors_upserted=len(point_ids),
            point_ids=point_ids,
        )


def run_indexing_cli(
    directory_path: str | Path | None = None,
    collection_name: str | None = None,
    batch_size: int | None = None,
    in_memory: bool = False,
    embedding_service: BaseEmbeddingService | None = None,
    vector_store_service: BaseVectorStoreService | None = None,
    raise_on_error: bool = True,
) -> IndexingCLIResult:
    """Synchronous CLI helper to ingest, chunk, embed, and index documents.

    Args:
        directory_path: Path to markdown documents directory (defaults to data/sample-documents).
        collection_name: Target vector collection name.
        batch_size: Batch size for embeddings and upserts.
        in_memory: If True, uses an in-memory Qdrant client and stub embeddings for offline execution.
        embedding_service: Optional custom BaseEmbeddingService.
        vector_store_service: Optional custom BaseVectorStoreService.
        raise_on_error: Whether to raise an exception on error (defaults to True).

    Returns:
        IndexingCLIResult: Subclass of tuple(documents, chunks, point_ids) with .result attribute.
    """
    import asyncio
    import hashlib

    target_dir = find_sample_documents_dir(directory_path)

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

    async def _execute() -> IndexingCLIResult:
        documents = await ingestion_service.ingest(target_dir)
        all_chunks: list[Chunk] = []
        for doc in documents:
            chunks = await ingestion_service.chunk_document(doc)
            all_chunks.extend(chunks)
        result = await indexing_service.index_documents(
            documents=documents,
            collection_name=collection_name,
            batch_size=batch_size,
            raise_on_error=raise_on_error,
        )
        return IndexingCLIResult(
            documents=documents,
            chunks=all_chunks,
            point_ids=result.point_ids,
            result=result,
        )

    return asyncio.run(_execute())


def execute_indexing_cli(args_list: list[str] | None = None) -> None:
    """Parse CLI arguments, execute indexing pipeline, and report structured results."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Index documents into Qdrant vector database."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Path to directory containing Markdown documents (defaults to discovered data/sample-documents).",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Target Qdrant collection name.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size for embedding generation and upsert.",
    )
    parser.add_argument(
        "--in-memory",
        action="store_true",
        help="Run completely offline using in-memory Qdrant and SHA256-stub embeddings (no API keys required).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress intermediate progress output.",
    )

    args = parser.parse_args(args_list)

    mode_label = "in-memory / offline mode" if args.in_memory else "live service mode"
    if not args.quiet:
        print(f"Starting document indexing pipeline ({mode_label})...")

    try:
        cli_result = run_indexing_cli(
            directory_path=args.directory,
            collection_name=args.collection,
            batch_size=args.batch_size,
            in_memory=args.in_memory,
            raise_on_error=False,
        )
    except Exception as exc:
        print(f"Error during indexing: {exc}", file=sys.stderr)
        sys.exit(1)

    result = cli_result.result
    chunks = cli_result.chunks
    point_ids = cli_result.point_ids

    print("\n--- Indexing Summary ---")
    print(f"Documents processed:  {result.documents_processed}")
    print(f"Chunks created:       {result.chunks_created}")
    print(f"Embeddings generated: {result.embeddings_generated}")
    print(f"Vectors upserted:     {result.vectors_upserted}")
    print(f"Failures:             {len(result.failures)}")

    if result.failures:
        print("\nFailure details:")
        for f in result.failures:
            doc_str = f" [doc: {f.document_id}]" if f.document_id else ""
            print(f"  - Stage: {f.stage}{doc_str} | Error: {f.error}")

    if point_ids and not args.quiet:
        print(f"\nSample point ID:      {point_ids[0]}")
        if chunks:
            print(f"Sample chunk ID:      {chunks[0].chunk_id}")
            print(f"Sample parent doc:    {chunks[0].document_id}")
            print(f"Sample text snippet:  {chunks[0].text[:100]}...")

    if result.has_failures and not result.is_success:
        sys.exit(1)


if __name__ == "__main__":
    execute_indexing_cli()

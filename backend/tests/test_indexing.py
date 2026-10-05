"""Comprehensive unit and integration tests for document embedding and Qdrant indexing pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from qdrant_client import QdrantClient

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.indexing import IndexingFailure, IndexingResult
from app.services.chunking import ChunkingService
from app.services.embedding import BaseEmbeddingService
from app.services.indexing import (
    BaseIndexingService,
    DocumentIndexingService,
    IndexingCLIResult,
    IndexingError,
    execute_indexing_cli,
    find_sample_documents_dir,
    run_indexing_cli,
)
from app.services.ingestion import DocumentIngestionService
from app.services.retrieval import QdrantRetrievalService
from app.services.vector_store import (
    BaseVectorStoreService,
    QdrantVectorStoreService,
)


class TestDocumentIndexingServiceMocked(unittest.IsolatedAsyncioTestCase):
    """Unit tests for DocumentIndexingService using mocked embedding and vector store dependencies."""

    def setUp(self) -> None:
        """Set up test fixtures with sample documents and chunks."""
        self.doc_1 = Document(
            document_id="doc_auth_guide",
            title="Authentication Architecture Guide",
            content="# Auth Guide\n\nConfigure OAuth2 and JWT authentication tokens for enterprise users.",
            source_type="markdown",
            source_path="docs/security/auth.md",
            product="SourceWise Core",
            version="2.1.0",
            department="Security",
            owner="sec-team@sourcewise.internal",
            access_level="internal",
            language="en",
            metadata={"priority": "high", "env": "prod"},
        )
        self.doc_2 = Document(
            document_id="doc_billing_runbook",
            title="Billing Runbook",
            content="# Billing\n\nStripe webhook event handling and invoice lifecycle management.",
            source_type="markdown",
            source_path="docs/finance/billing.md",
            product="Billing Engine",
            version="1.0.0",
            department="Finance",
            owner="billing-team@sourcewise.internal",
            access_level="confidential",
            language="en",
            metadata={"billing_cycle": "monthly"},
        )

        self.sample_chunk_1 = Chunk(
            chunk_id="doc_auth_guide#chunk_0",
            document_id="doc_auth_guide",
            text="Configure OAuth2 and JWT authentication tokens.",
            chunk_index=0,
            token_count=8,
            metadata={
                "document_id": "doc_auth_guide",
                "chunk_id": "doc_auth_guide#chunk_0",
                "chunk_index": 0,
                "title": "Authentication Architecture Guide",
                "source_type": "markdown",
                "product": "SourceWise Core",
                "version": "2.1.0",
                "department": "Security",
                "owner": "sec-team@sourcewise.internal",
                "last_updated": None,
                "access_level": "internal",
                "language": "en",
                "source_path": "docs/security/auth.md",
                "priority": "high",
            },
        )
        self.sample_chunk_2 = Chunk(
            chunk_id="doc_auth_guide#chunk_1",
            document_id="doc_auth_guide",
            text="Refresh token rotation and revocation procedures.",
            chunk_index=1,
            token_count=7,
            metadata={
                "document_id": "doc_auth_guide",
                "chunk_id": "doc_auth_guide#chunk_1",
                "chunk_index": 1,
                "title": "Authentication Architecture Guide",
                "source_type": "markdown",
                "product": "SourceWise Core",
                "version": "2.1.0",
                "department": "Security",
                "owner": "sec-team@sourcewise.internal",
                "last_updated": None,
                "access_level": "internal",
                "language": "en",
                "source_path": "docs/security/auth.md",
                "priority": "high",
            },
        )
        self.sample_chunk_3 = Chunk(
            chunk_id="doc_billing_runbook#chunk_0",
            document_id="doc_billing_runbook",
            text="Stripe webhook event handling and invoice reconciliation.",
            chunk_index=0,
            token_count=8,
            metadata={
                "document_id": "doc_billing_runbook",
                "chunk_id": "doc_billing_runbook#chunk_0",
                "chunk_index": 0,
                "title": "Billing Runbook",
                "source_type": "markdown",
                "product": "Billing Engine",
                "version": "1.0.0",
                "department": "Finance",
                "owner": "billing-team@sourcewise.internal",
                "last_updated": None,
                "access_level": "confidential",
                "language": "en",
                "source_path": "docs/finance/billing.md",
                "billing_cycle": "monthly",
            },
        )

    async def test_document_indexing_flow(self) -> None:
        """Verify full document indexing: doc -> chunker -> batch embedder -> vector store."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
        ]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.create_collection_if_not_exists.return_value = True
        mock_vector_store.store_chunks.return_value = ["point_uuid_1", "point_uuid_2"]

        mock_chunking = MagicMock(spec=DocumentIngestionService)
        mock_chunking.chunk_document = AsyncMock(
            return_value=[self.sample_chunk_1, self.sample_chunk_2]
        )

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        result = await service.index_documents(self.doc_1, collection_name="test_col")

        # Verify structured result
        self.assertIsInstance(result, IndexingResult)
        self.assertEqual(result.documents_processed, 1)
        self.assertEqual(result.chunks_created, 2)
        self.assertEqual(result.chunks_indexed, 2)
        self.assertEqual(result.point_ids, ["point_uuid_1", "point_uuid_2"])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        self.assertTrue(result.is_success)

        # Backward-compatible comparison
        self.assertEqual(result, ["point_uuid_1", "point_uuid_2"])

        mock_chunking.chunk_document.assert_awaited_once_with(self.doc_1)
        mock_embedding.embed_texts.assert_called_once_with(
            [self.sample_chunk_1.text, self.sample_chunk_2.text]
        )
        mock_vector_store.create_collection_if_not_exists.assert_called_once_with(
            collection_name="test_col",
            vector_size=4,
        )
        mock_vector_store.store_chunks.assert_called_once_with(
            chunks=[self.sample_chunk_1, self.sample_chunk_2],
            vectors=[[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]],
            collection_name="test_col",
        )

    async def test_multiple_documents_indexing(self) -> None:
        """Verify indexing multiple documents in a single invocation."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6],
        ]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.create_collection_if_not_exists.return_value = True
        mock_vector_store.store_chunks.return_value = ["point_1", "point_2", "point_3"]

        mock_chunking = MagicMock(spec=DocumentIngestionService)

        async def _mock_chunk(doc: Document, **kwargs):
            if doc.document_id == "doc_auth_guide":
                return [self.sample_chunk_1, self.sample_chunk_2]
            return [self.sample_chunk_3]

        mock_chunking.chunk_document = AsyncMock(side_effect=_mock_chunk)

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        result = await service.index_documents([self.doc_1, self.doc_2], collection_name="multi_col")

        self.assertIsInstance(result, IndexingResult)
        self.assertEqual(result.documents_processed, 2)
        self.assertEqual(result.chunks_created, 3)
        self.assertEqual(result.chunks_indexed, 3)
        self.assertEqual(result.point_ids, ["point_1", "point_2", "point_3"])
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.errors), 0)

        # Chunker called for both documents
        self.assertEqual(mock_chunking.chunk_document.await_count, 2)
        # Vector store called with all 3 chunks
        self.assertEqual(mock_vector_store.store_chunks.call_count, 1)

    async def test_chunk_indexing_directly(self) -> None:
        """Verify index_chunks embeds and stores pre-segmented chunks without invoking chunker."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.store_chunks.return_value = ["point_1"]

        mock_chunking = MagicMock(spec=DocumentIngestionService)

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        point_ids = await service.index_chunks([self.sample_chunk_1])

        self.assertEqual(point_ids, ["point_1"])
        mock_embedding.embed_texts.assert_called_once_with([self.sample_chunk_1.text])
        mock_vector_store.store_chunks.assert_called_once()
        # Chunker should not be called when indexing chunks directly
        self.assertEqual(len(mock_chunking.method_calls), 0)

    async def test_batch_embedding_processing(self) -> None:
        """Verify batching: chunks are embedded and upserted in batches without 1 request per chunk."""
        # 5 chunks with batch_size=2 -> 3 batch calls: [2, 2, 1]
        chunks = [
            Chunk(
                chunk_id=f"doc_test#chunk_{i}",
                document_id="doc_test",
                text=f"Sample text content for chunk {i}",
                chunk_index=i,
            )
            for i in range(5)
        ]

        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.side_effect = [
            [[0.1] * 4, [0.2] * 4],
            [[0.3] * 4, [0.4] * 4],
            [[0.5] * 4],
        ]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.store_chunks.side_effect = [
            ["p0", "p1"],
            ["p2", "p3"],
            ["p4"],
        ]

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            batch_size=2,
        )

        point_ids = await service.index_chunks(chunks)

        self.assertEqual(point_ids, ["p0", "p1", "p2", "p3", "p4"])
        self.assertEqual(mock_embedding.embed_texts.call_count, 3)
        self.assertEqual(mock_vector_store.store_chunks.call_count, 3)
        # embed_text (single) must NOT be called
        self.assertEqual(mock_embedding.embed_text.call_count, 0)

        # Verify batch call arguments
        first_call_texts = mock_embedding.embed_texts.call_args_list[0][0][0]
        self.assertEqual(len(first_call_texts), 2)
        second_call_texts = mock_embedding.embed_texts.call_args_list[1][0][0]
        self.assertEqual(len(second_call_texts), 2)
        third_call_texts = mock_embedding.embed_texts.call_args_list[2][0][0]
        self.assertEqual(len(third_call_texts), 1)

    async def test_vector_store_interaction(self) -> None:
        """Verify vector store receives the exact chunks, generated vectors, and collection configuration."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.store_chunks.return_value = ["point_abc"]

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        point_ids = await service.index_chunks(
            chunks=[self.sample_chunk_1],
            collection_name="custom_collection",
        )

        self.assertEqual(point_ids, ["point_abc"])
        mock_vector_store.create_collection_if_not_exists.assert_called_once_with(
            collection_name="custom_collection",
            vector_size=3,
        )
        mock_vector_store.store_chunks.assert_called_once_with(
            chunks=[self.sample_chunk_1],
            vectors=[[0.1, 0.2, 0.3]],
            collection_name="custom_collection",
        )

    async def test_empty_documents_handling(self) -> None:
        """Verify empty documents or empty chunk lists return structured empty results."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_chunking = MagicMock(spec=DocumentIngestionService)
        mock_chunking.chunk_document = AsyncMock(return_value=[])

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        # 1. Empty document list
        result1 = await service.index_documents([])
        self.assertEqual(result1.documents_processed, 0)
        self.assertEqual(result1.chunks_created, 0)
        self.assertEqual(result1.chunks_indexed, 0)
        self.assertEqual(result1.point_ids, [])
        self.assertEqual(result1, [])

        # 2. Document yielding zero chunks
        result2 = await service.index_documents(self.doc_1)
        self.assertEqual(result2.documents_processed, 1)
        self.assertEqual(result2.chunks_created, 0)
        self.assertEqual(result2.chunks_indexed, 0)
        self.assertEqual(result2.point_ids, [])
        self.assertEqual(result2, [])

        # 3. Empty chunks list
        result3 = await service.index_chunks([])
        self.assertEqual(result3, [])

        # Verify embedding and vector store were never called
        self.assertEqual(mock_embedding.embed_texts.call_count, 0)
        self.assertEqual(mock_vector_store.store_chunks.call_count, 0)

    async def test_deterministic_reindexing(self) -> None:
        """Verify deterministic indexing: re-indexing the same chunk produces identical UUID point IDs and updates in-place."""
        real_vector_store = QdrantVectorStoreService(client=QdrantClient(":memory:"), vector_size=3)
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[1.0, 0.0, 0.0]]

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=real_vector_store,
        )

        # First indexing run
        point_ids_run1 = await service.index_chunks([self.sample_chunk_1])

        # Second indexing run on same chunk
        point_ids_run2 = await service.index_chunks([self.sample_chunk_1])

        # Both runs must produce identical deterministic UUIDs
        self.assertEqual(point_ids_run1, point_ids_run2)
        expected_uuid = QdrantVectorStoreService.chunk_id_to_point_id(self.sample_chunk_1.chunk_id)
        self.assertEqual(point_ids_run1[0], expected_uuid)

        # Total points in vector store must still be exactly 1 (no duplicate points created)
        count_res = real_vector_store.client.count(
            collection_name=real_vector_store.collection_name
        )
        self.assertEqual(count_res.count, 1)

    async def test_metadata_preservation(self) -> None:
        """Verify all 13 required metadata fields are completely preserved without silent discarding."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[0.1, 0.2]]

        stored_chunks_capture: list[Chunk] = []

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)

        def capture_store_chunks(chunks, vectors, **kwargs):
            stored_chunks_capture.extend(chunks)
            return ["point_meta_1"]

        mock_vector_store.store_chunks.side_effect = capture_store_chunks

        # Use real chunking service to verify Document -> Chunk metadata inheritance
        chunker = ChunkingService()
        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=chunker,
        )

        result = await service.index_documents(self.doc_1)
        self.assertEqual(result.documents_processed, 1)
        self.assertGreaterEqual(result.chunks_created, 1)

        self.assertGreaterEqual(len(stored_chunks_capture), 1)
        captured = stored_chunks_capture[0]

        # Verify all 13 required metadata fields on the chunk
        required_fields = [
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
        ]
        for field in required_fields:
            self.assertIn(
                field,
                captured.metadata,
                f"Required metadata field '{field}' was silently discarded from chunk.metadata",
            )

        # Specific values verification
        self.assertEqual(captured.document_id, "doc_auth_guide")
        self.assertEqual(captured.chunk_id, "doc_auth_guide#chunk_0")
        self.assertEqual(captured.chunk_index, 0)
        self.assertEqual(captured.metadata["document_id"], "doc_auth_guide")
        self.assertEqual(captured.metadata["chunk_id"], "doc_auth_guide#chunk_0")
        self.assertEqual(captured.metadata["chunk_index"], 0)
        self.assertEqual(captured.metadata["title"], "Authentication Architecture Guide")
        self.assertEqual(captured.metadata["source_type"], "markdown")
        self.assertEqual(captured.metadata["product"], "SourceWise Core")
        self.assertEqual(captured.metadata["version"], "2.1.0")
        self.assertEqual(captured.metadata["department"], "Security")
        self.assertEqual(captured.metadata["owner"], "sec-team@sourcewise.internal")
        self.assertEqual(captured.metadata["access_level"], "internal")
        self.assertEqual(captured.metadata["language"], "en")
        self.assertEqual(captured.metadata["source_path"], "docs/security/auth.md")
        self.assertEqual(captured.metadata["priority"], "high")

        # Verify Qdrant payload construction preserves all 13 fields in metadata dict
        payload = QdrantVectorStoreService(client=QdrantClient(":memory:")).build_payload(captured)
        for field in required_fields:
            self.assertIn(field, payload["metadata"], f"Required field '{field}' missing from payload metadata dict")

        # Verify core provenance identifiers at top level of payload
        self.assertEqual(payload["document_id"], "doc_auth_guide")
        self.assertEqual(payload["chunk_id"], "doc_auth_guide#chunk_0")
        self.assertEqual(payload["chunk_index"], 0)

    async def test_embedding_vector_count_mismatch(self) -> None:
        """Verify ValueError is raised if embedding service returns vector count != chunk count."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        # 2 chunks provided, but embedding service only returns 1 vector
        mock_embedding.embed_texts.return_value = [[0.1, 0.2]]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        with self.assertRaises(ValueError) as ctx:
            await service.index_chunks([self.sample_chunk_1, self.sample_chunk_2])

        self.assertIn("Embedding count mismatch", str(ctx.exception))
        # Vector store should not have been called
        self.assertEqual(mock_vector_store.store_chunks.call_count, 0)

    async def test_indexing_failure_handling_embedding_error(self) -> None:
        """Verify clean failure handling and reporting when embedding service fails."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.side_effect = RuntimeError("Embedding provider rate limited (HTTP 429)")

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)

        mock_chunking = MagicMock(spec=DocumentIngestionService)
        mock_chunking.chunk_document = AsyncMock(return_value=[self.sample_chunk_1])

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        # 1. Direct index_chunks raises IndexingError
        with self.assertRaises(IndexingError) as ctx:
            await service.index_chunks([self.sample_chunk_1])
        self.assertIn("Embedding generation failed", str(ctx.exception))

        # 2. index_documents with raise_on_error=False records failure without silent success
        result = await service.index_documents(self.doc_1, raise_on_error=False)
        self.assertFalse(result.is_success)
        self.assertTrue(result.has_failures)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Embedding generation failed", result.errors[0])
        self.assertEqual(result.failures[0].stage, "storage")
        self.assertEqual(result.chunks_indexed, 0)

        # 3. index_documents with raise_on_error=True raises IndexingError
        with self.assertRaises(IndexingError):
            await service.index_documents(self.doc_1, raise_on_error=True)

    async def test_indexing_failure_handling_vector_store_error(self) -> None:
        """Verify clean failure handling and reporting when vector store upsert fails."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[0.1, 0.2]]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.store_chunks.side_effect = RuntimeError("Qdrant connection refused")

        mock_chunking = MagicMock(spec=DocumentIngestionService)
        mock_chunking.chunk_document = AsyncMock(return_value=[self.sample_chunk_1])

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        # 1. Direct index_chunks raises IndexingError
        with self.assertRaises(IndexingError) as ctx:
            await service.index_chunks([self.sample_chunk_1])
        self.assertIn("Vector store upsert failed", str(ctx.exception))

        # 2. index_documents captures failure cleanly
        result = await service.index_documents(self.doc_1, raise_on_error=False)
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Vector store upsert failed", result.errors[0])
        self.assertEqual(result.chunks_indexed, 0)

    async def test_indexing_failure_handling_partial_document_failure(self) -> None:
        """Verify failure for one document produces useful error rather than silently succeeding."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[0.1, 0.2]]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.store_chunks.return_value = ["point_1"]

        mock_chunking = MagicMock(spec=DocumentIngestionService)

        async def _chunk_mock(doc: Document, **kwargs):
            if doc.document_id == "doc_auth_guide":
                return [self.sample_chunk_1]
            raise ValueError(f"Corrupted syntax in document '{doc.document_id}'")

        mock_chunking.chunk_document = AsyncMock(side_effect=_chunk_mock)

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=mock_chunking,
        )

        result = await service.index_documents([self.doc_1, self.doc_2], raise_on_error=False)

        # Did NOT silently succeed
        self.assertFalse(result.is_success)
        self.assertTrue(result.has_failures)

        # doc_1 was processed and indexed
        self.assertEqual(result.documents_processed, 1)
        self.assertEqual(result.chunks_created, 1)
        self.assertEqual(result.chunks_indexed, 1)
        self.assertEqual(result.point_ids, ["point_1"])

        # doc_2 failure was captured with useful context
        self.assertEqual(len(result.errors), 1)
        self.assertIn("doc_billing_runbook", result.errors[0])
        self.assertIn("Corrupted syntax", result.errors[0])
        self.assertEqual(result.failures[0].document_id, "doc_billing_runbook")
        self.assertEqual(result.failures[0].stage, "chunking")

    async def test_invalid_arguments_handling(self) -> None:
        """Verify validation of batch_size and document type."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        with self.assertRaises(ValueError):
            await service.index_chunks([self.sample_chunk_1], batch_size=0)

        with self.assertRaises(ValueError):
            await service.index_chunks([self.sample_chunk_1], batch_size=-5)

        with self.assertRaises(TypeError):
            await service.index_documents(["not_a_document_object"])  # type: ignore[list-item]


class TestOfflineIndexingIntegration(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration test verifying the complete offline pipeline:

    Document -> Chunks -> Vectors -> Qdrant -> Retrievable Evidence
    """

    def setUp(self) -> None:
        """Set up in-memory Qdrant and sample documents directory."""
        self.sample_docs_dir = (
            Path(__file__).resolve().parent.parent.parent / "data" / "sample-documents"
        )
        self.in_memory_client = QdrantClient(":memory:")
        self.collection_name = "test_offline_rag_index"
        self.vector_dim = 8

        # Deterministic offline stub embedding service
        class StubEmbeddingService(BaseEmbeddingService):
            def __init__(self, dim: int = 8) -> None:
                self.dim = dim

            def _hash_vector(self, text: str) -> list[float]:
                raw = text.lower()
                h = hashlib.sha256(raw.encode("utf-8")).digest()
                vec = [(b / 128.0) - 1.0 for b in h[: self.dim]]
                # Boost specific dimensions based on keyword presence for semantic retrieval test
                if "rate limit" in raw or "quota" in raw or "throttle" in raw:
                    vec[0] += 2.0
                if "auth" in raw or "oauth" in raw or "token" in raw:
                    vec[1] += 2.0
                if "login" in raw or "sso" in raw or "password" in raw:
                    vec[2] += 2.0
                return vec

            def embed_text(self, text: str) -> list[float]:
                return self._hash_vector(text)

            def embed_texts(self, texts: list[str]) -> list[list[float]]:
                return [self._hash_vector(t) for t in texts]

            def query_embedding(self, query: str) -> list[float]:
                return self._hash_vector(query)

        self.stub_embedding = StubEmbeddingService(dim=self.vector_dim)
        self.vector_store = QdrantVectorStoreService(
            client=self.in_memory_client,
            collection_name=self.collection_name,
            vector_size=self.vector_dim,
        )
        self.ingestion_service = DocumentIngestionService()
        self.indexing_service = DocumentIndexingService(
            embedding_service=self.stub_embedding,
            vector_store_service=self.vector_store,
            chunking_service=self.ingestion_service,
            batch_size=4,
        )

    async def test_offline_document_indexing_and_retrieval_flow(self) -> None:
        """Verify: document -> chunks -> vectors -> Qdrant -> retrievable evidence."""
        # 1. Ingest actual sample documents
        documents = await self.ingestion_service.ingest(self.sample_docs_dir)
        self.assertGreaterEqual(len(documents), 3)

        # 2. Index documents via DocumentIndexingService
        result = await self.indexing_service.index_documents(
            documents=documents,
            collection_name=self.collection_name,
        )

        self.assertIsInstance(result, IndexingResult)
        self.assertTrue(result.is_success)
        self.assertEqual(result.documents_processed, len(documents))
        self.assertGreaterEqual(result.chunks_created, 6)
        self.assertEqual(result.chunks_indexed, result.chunks_created)
        point_ids = result.point_ids
        self.assertTrue(point_ids)

        # 3. Verify points in Qdrant
        count_res = self.in_memory_client.count(collection_name=self.collection_name)
        self.assertEqual(count_res.count, len(point_ids))

        # 4. Verify idempotence: re-indexing the same documents must not create duplicate points
        repeated_result = await self.indexing_service.index_documents(
            documents=documents,
            collection_name=self.collection_name,
        )
        self.assertEqual(repeated_result.point_ids, point_ids)

        recount_res = self.in_memory_client.count(collection_name=self.collection_name)
        self.assertEqual(
            recount_res.count,
            len(point_ids),
            "Repeated indexing must update in-place without duplicating vector points",
        )

        # 5. Verify semantic retrieval of evidence via QdrantRetrievalService
        retrieval_service = QdrantRetrievalService(
            embedding_service=self.stub_embedding,
            vector_store_service=self.vector_store,
        )

        # Query 1: Rate limit query
        evidence_rate_limit = await retrieval_service.retrieve(
            query="API rate limits and quota throttling rules",
            top_k=2,
            collection_name=self.collection_name,
        )

        self.assertGreaterEqual(len(evidence_rate_limit), 1)
        top_rate_chunk = evidence_rate_limit[0]
        self.assertEqual(top_rate_chunk.rank, 1)
        self.assertIn("sample-api-rate-limits", top_rate_chunk.document_id)
        self.assertTrue(top_rate_chunk.text)
        self.assertTrue(top_rate_chunk.chunk_id)
        # Verify metadata preservation on retrieved evidence
        self.assertEqual(
            top_rate_chunk.chunk.metadata.get("title"),
            "API Rate Limits and Quota Management",
        )
        self.assertEqual(
            top_rate_chunk.chunk.metadata.get("product"),
            "SourceWise Platform",
        )
        self.assertEqual(
            top_rate_chunk.chunk.metadata.get("access_level"),
            "internal",
        )
        self.assertEqual(
            top_rate_chunk.chunk.metadata.get("document_id"),
            top_rate_chunk.document_id,
        )
        self.assertEqual(
            top_rate_chunk.chunk.metadata.get("chunk_id"),
            top_rate_chunk.chunk_id,
        )

        # Query 2: Auth query with metadata filter
        evidence_auth = await retrieval_service.retrieve(
            query="enterprise OAuth2 tokens and authentication",
            top_k=3,
            filters={"document_id": "sample-authentication-guide"},
            collection_name=self.collection_name,
        )

        self.assertGreaterEqual(len(evidence_auth), 1)
        for ev in evidence_auth:
            self.assertEqual(ev.document_id, "sample-authentication-guide")
            self.assertEqual(ev.chunk.metadata.get("department"), "Engineering")
            self.assertEqual(ev.chunk.metadata.get("language"), "en")

    def test_run_indexing_cli_offline(self) -> None:
        """Verify the synchronous CLI helper functions cleanly in offline mode."""
        docs, chunks, point_ids = run_indexing_cli(
            directory_path=str(self.sample_docs_dir),
            collection_name="cli_test_collection",
            in_memory=True,
            batch_size=4,
        )

        self.assertGreaterEqual(len(docs), 3)
        self.assertGreaterEqual(len(chunks), 6)
        self.assertEqual(len(point_ids), len(chunks))


class TestPR17ProductionIndexingRequirements(unittest.IsolatedAsyncioTestCase):
    """Targeted tests for PR 17 requirements:

    1. Document discovery
    2. Metadata extraction
    3. Chunking
    4. Deterministic IDs
    5. Repeated indexing (idempotency)
    6. Metadata preservation (all 11 fields)
    7. Embedding batching
    8. Vector upsert
    9. Failure handling and structured reporting
    10. Demo knowledge-base coherence
    """

    def setUp(self) -> None:
        self.sample_docs_dir = (
            Path(__file__).resolve().parent.parent.parent / "data" / "sample-documents"
        )
        self.in_memory_client = QdrantClient(":memory:")

    def test_document_discovery(self) -> None:
        """Verify document discovery locates sample documents directory and files."""
        # 1. Automatic discovery locates data/sample-documents
        discovered_dir = find_sample_documents_dir()
        self.assertTrue(discovered_dir.exists())
        self.assertTrue(discovered_dir.is_dir())

        # Verify Markdown files present
        md_files = list(discovered_dir.glob("*.md"))
        file_names = {f.name for f in md_files}
        self.assertIn("api-rate-limits.md", file_names)
        self.assertIn("product-authentication-guide.md", file_names)
        self.assertIn("support-login-troubleshooting.md", file_names)

        # 2. Custom valid directory
        custom_dir = find_sample_documents_dir(str(self.sample_docs_dir))
        self.assertEqual(custom_dir, self.sample_docs_dir.resolve())

        # 3. Invalid directory raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            find_sample_documents_dir("non_existent_folder_abc_123")

    async def test_metadata_extraction(self) -> None:
        """Verify metadata extraction parses frontmatter into canonical Document model."""
        ingestion = DocumentIngestionService()
        documents = await ingestion.ingest(self.sample_docs_dir)

        docs_by_id = {doc.document_id: doc for doc in documents}
        self.assertIn("sample-api-rate-limits", docs_by_id)
        self.assertIn("sample-authentication-guide", docs_by_id)
        self.assertIn("sample-login-troubleshooting", docs_by_id)

        rate_limit_doc = docs_by_id["sample-api-rate-limits"]
        self.assertEqual(rate_limit_doc.title, "API Rate Limits and Quota Management")
        self.assertEqual(rate_limit_doc.source_type, "product_documentation")
        self.assertEqual(rate_limit_doc.product, "SourceWise Platform")
        self.assertEqual(rate_limit_doc.version, "2.0")
        self.assertEqual(rate_limit_doc.department, "Engineering")
        self.assertEqual(rate_limit_doc.owner, "API Infrastructure Team")
        self.assertEqual(str(rate_limit_doc.last_updated), "2026-09-14")
        self.assertEqual(rate_limit_doc.access_level, "internal")
        self.assertEqual(rate_limit_doc.language, "en")

    async def test_chunking(self) -> None:
        """Verify chunking segments documents into traceable chunks with correct indexes."""
        ingestion = DocumentIngestionService()
        documents = await ingestion.ingest(self.sample_docs_dir)

        total_chunks = 0
        for doc in documents:
            chunks = await ingestion.chunk_document(doc)
            self.assertGreater(len(chunks), 0)
            total_chunks += len(chunks)
            for idx, chunk in enumerate(chunks):
                self.assertEqual(chunk.chunk_index, idx)
                self.assertEqual(chunk.chunk_id, f"{doc.document_id}#chunk_{idx}")
                self.assertEqual(chunk.document_id, doc.document_id)
                self.assertTrue(chunk.text.strip())
                self.assertIsNotNone(chunk.token_count)
                self.assertGreater(chunk.token_count, 0)
        self.assertGreaterEqual(total_chunks, 6)

    def test_deterministic_ids(self) -> None:
        """Verify chunk_id and UUIDv5 point IDs are deterministic and reproducible."""
        chunk_id = "sample-auth-guide#chunk_2"
        point_id_1 = QdrantVectorStoreService.chunk_id_to_point_id(chunk_id)
        point_id_2 = QdrantVectorStoreService.chunk_id_to_point_id(chunk_id)

        self.assertEqual(point_id_1, point_id_2)
        # Distinct chunk IDs produce distinct point IDs
        other_point_id = QdrantVectorStoreService.chunk_id_to_point_id("sample-auth-guide#chunk_3")
        self.assertNotEqual(point_id_1, other_point_id)

    async def test_repeated_indexing_idempotency(self) -> None:
        """Verify running indexing multiple times with the same documents does not create duplicate vectors."""
        vector_store = QdrantVectorStoreService(
            client=self.in_memory_client,
            collection_name="test_idempotent_indexing",
            vector_size=8,
        )

        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.return_value = [[0.1] * 8, [0.2] * 8]

        sample_chunk_a = Chunk(
            chunk_id="doc_idem#chunk_0",
            document_id="doc_idem",
            text="First chunk content.",
            chunk_index=0,
            token_count=3,
        )
        sample_chunk_b = Chunk(
            chunk_id="doc_idem#chunk_1",
            document_id="doc_idem",
            text="Second chunk content.",
            chunk_index=1,
            token_count=3,
        )

        indexing_service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=vector_store,
            batch_size=2,
        )

        # First run
        points_run1 = await indexing_service.index_chunks([sample_chunk_a, sample_chunk_b])
        self.assertEqual(len(points_run1), 2)

        count_1 = self.in_memory_client.count("test_idempotent_indexing").count
        self.assertEqual(count_1, 2)

        # Second run (re-indexing identical chunks)
        points_run2 = await indexing_service.index_chunks([sample_chunk_a, sample_chunk_b])
        self.assertEqual(points_run1, points_run2)

        count_2 = self.in_memory_client.count("test_idempotent_indexing").count
        self.assertEqual(count_2, 2, "Points count must remain 2 after re-indexing; no duplicates allowed.")

    async def test_metadata_preservation_through_pipeline(self) -> None:
        """Verify all 11 required metadata fields are preserved through Document -> Chunk -> Vector payload -> RetrievedChunk."""
        vector_store = QdrantVectorStoreService(
            client=QdrantClient(":memory:"),
            collection_name="test_meta_preservation",
            vector_size=4,
        )

        class FixedEmbedding(BaseEmbeddingService):
            def embed_text(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3, 0.4]

            def embed_texts(self, texts: list[str]) -> list[list[float]]:
                return [self.embed_text(t) for t in texts]

            def query_embedding(self, query: str) -> list[float]:
                return self.embed_text(query)

        emb_service = FixedEmbedding()
        indexing_service = DocumentIndexingService(
            embedding_service=emb_service,
            vector_store_service=vector_store,
        )

        test_doc = Document(
            document_id="doc_preserve_test",
            title="Preservation Test Doc",
            content="# Title\n\nContent for testing metadata preservation.",
            source_type="product_documentation",
            product="SourceWise Core",
            version="3.0",
            department="DevRel",
            owner="devrel@sourcewise.internal",
            last_updated="2026-09-20",
            access_level="public",
            language="en",
            source_path="docs/test.md",
        )

        result = await indexing_service.index_documents(test_doc)
        self.assertTrue(result.is_success)
        self.assertEqual(result.documents_processed, 1)
        self.assertGreaterEqual(result.vectors_upserted, 1)

        retrieval = QdrantRetrievalService(
            embedding_service=emb_service,
            vector_store_service=vector_store,
        )

        retrieved = await retrieval.retrieve("Preservation Test", top_k=1)
        self.assertEqual(len(retrieved), 1)
        item = retrieved[0]

        # Verify all 11 target fields
        self.assertEqual(item.document_id, "doc_preserve_test")
        self.assertEqual(item.title, "Preservation Test Doc")
        self.assertEqual(item.source_type, "product_documentation")
        self.assertEqual(item.product, "SourceWise Core")
        self.assertEqual(item.version, "3.0")
        self.assertEqual(item.department, "DevRel")
        self.assertEqual(item.owner, "devrel@sourcewise.internal")
        self.assertEqual(str(item.last_updated), "2026-09-20")
        self.assertEqual(item.access_level, "public")
        self.assertEqual(item.language, "en")
        self.assertEqual(item.source_path, "docs/test.md")

    async def test_embedding_batching(self) -> None:
        """Verify embedding batching processes chunks in configured batch sizes without skipping."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        # 7 chunks with batch_size=3 -> [3, 3, 1]
        mock_embedding.embed_texts.side_effect = [
            [[0.1] * 4, [0.2] * 4, [0.3] * 4],
            [[0.4] * 4, [0.5] * 4, [0.6] * 4],
            [[0.7] * 4],
        ]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.store_chunks.side_effect = [
            ["p0", "p1", "p2"],
            ["p3", "p4", "p5"],
            ["p6"],
        ]

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            batch_size=3,
        )

        chunks = [
            Chunk(
                chunk_id=f"test_batch#chunk_{i}",
                document_id="test_batch",
                text=f"Batch chunk text {i}",
                chunk_index=i,
            )
            for i in range(7)
        ]

        point_ids = await service.index_chunks(chunks)
        self.assertEqual(len(point_ids), 7)
        self.assertEqual(mock_embedding.embed_texts.call_count, 3)

        batch_sizes = [len(call[0][0]) for call in mock_embedding.embed_texts.call_args_list]
        self.assertEqual(batch_sizes, [3, 3, 1])

    async def test_vector_upsert_payload(self) -> None:
        """Verify vector upsert stores properly formatted payloads in vector database."""
        client = QdrantClient(":memory:")
        vector_store = QdrantVectorStoreService(
            client=client,
            collection_name="test_upsert_payload_collection",
            vector_size=4,
        )

        chunk = Chunk(
            chunk_id="doc_upsert#chunk_0",
            document_id="doc_upsert",
            text="Upsert payload test content",
            chunk_index=0,
            token_count=4,
            metadata={"title": "Upsert Title", "owner": "Owner A"},
        )

        point_ids = vector_store.store_chunks(
            chunks=[chunk],
            vectors=[[0.1, 0.2, 0.3, 0.4]],
        )

        self.assertEqual(len(point_ids), 1)
        point_id = point_ids[0]

        retrieved_point = client.retrieve(
            collection_name="test_upsert_payload_collection",
            ids=[point_id],
            with_payload=True,
        )
        self.assertEqual(len(retrieved_point), 1)
        p = retrieved_point[0]
        self.assertEqual(p.payload["chunk_id"], "doc_upsert#chunk_0")
        self.assertEqual(p.payload["document_id"], "doc_upsert")
        self.assertEqual(p.payload["text"], "Upsert payload test content")
        self.assertEqual(p.payload["chunk_index"], 0)
        self.assertEqual(p.payload["metadata"]["title"], "Upsert Title")

    async def test_failure_handling_and_structured_result(self) -> None:
        """Verify failure handling reports structured IndexingResult with failures."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.embed_texts.side_effect = RuntimeError("Embedding service unavailable (HTTP 503)")

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)

        service = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        test_doc = Document(
            document_id="doc_fail_test",
            title="Fail Test",
            content="Content for failure testing",
        )

        result = await service.index_documents(test_doc, raise_on_error=False)

        self.assertFalse(result.is_success)
        self.assertTrue(result.has_failures)
        self.assertEqual(result.documents_processed, 1)
        self.assertEqual(result.chunks_indexed, 0)
        self.assertEqual(result.vectors_upserted, 0)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failures[0].stage, "storage")
        self.assertIn("Embedding service unavailable", result.failures[0].error)

    async def test_demo_knowledge_base_queries(self) -> None:
        """Verify the 3 core demo questions retrieve coherent evidence from the demo documents."""
        client = QdrantClient(":memory:")
        VOCAB = ["troubleshoot", "login", "failure", "rate", "limit", "authentication", "oauth", "quota"]
        vector_dim = len(VOCAB)
        col_name = "test_demo_kb_collection"

        class VocabEmbedding(BaseEmbeddingService):
            def _embed(self, text: str) -> list[float]:
                raw = text.lower()
                vec = [float(raw.count(w)) for w in VOCAB]
                if sum(v * v for v in vec) == 0:
                    vec = [0.001] * len(VOCAB)
                return vec

            def embed_text(self, text: str) -> list[float]:
                return self._embed(text)

            def embed_texts(self, texts: list[str]) -> list[list[float]]:
                return [self._embed(t) for t in texts]

            def query_embedding(self, query: str) -> list[float]:
                return self._embed(query)

        emb_service = VocabEmbedding()
        vs_service = QdrantVectorStoreService(
            client=client,
            collection_name=col_name,
            vector_size=vector_dim,
        )
        ingestion = DocumentIngestionService()
        indexing = DocumentIndexingService(
            embedding_service=emb_service,
            vector_store_service=vs_service,
            chunking_service=ingestion,
        )

        # Ingest and index all sample documents
        docs = await ingestion.ingest(self.sample_docs_dir)
        result = await indexing.index_documents(docs, collection_name=col_name)
        self.assertTrue(result.is_success)
        self.assertEqual(result.documents_processed, 3)

        retrieval = QdrantRetrievalService(
            embedding_service=emb_service,
            vector_store_service=vs_service,
        )

        # 1. "How do I troubleshoot login failures?"
        login_res = await retrieval.retrieve("How do I troubleshoot login failures?", top_k=2, collection_name=col_name)
        self.assertGreaterEqual(len(login_res), 1)
        self.assertEqual(login_res[0].document_id, "sample-login-troubleshooting")
        self.assertIn("login", login_res[0].text.lower())

        # 2. "What are the API rate limits?"
        rate_res = await retrieval.retrieve("What are the API rate limits?", top_k=2, collection_name=col_name)
        self.assertGreaterEqual(len(rate_res), 1)
        self.assertEqual(rate_res[0].document_id, "sample-api-rate-limits")
        self.assertIn("rate limit", rate_res[0].text.lower())

        # 3. "How does authentication work?"
        auth_res = await retrieval.retrieve("How does authentication work?", top_k=2, collection_name=col_name)
        self.assertGreaterEqual(len(auth_res), 1)
        self.assertEqual(auth_res[0].document_id, "sample-authentication-guide")
        self.assertIn("auth", auth_res[0].text.lower())

    async def test_dry_run_mode_service(self) -> None:
        """Verify dry-run mode chunks documents without calling embedding or vector store."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        ingestion = DocumentIngestionService()

        indexing = DocumentIndexingService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
            chunking_service=ingestion,
        )

        docs = await ingestion.ingest(self.sample_docs_dir)
        result = await indexing.index_documents(docs, dry_run=True)

        self.assertEqual(result.documents_processed, len(docs))
        self.assertGreater(result.chunks_created, 0)
        self.assertEqual(result.embeddings_generated, 0)
        self.assertEqual(result.vectors_upserted, 0)
        self.assertEqual(result.chunks_indexed, 0)
        self.assertEqual(result.point_ids, [])
        self.assertTrue(result.is_success)

        # Ensure embedding and vector store were never called
        self.assertEqual(mock_embedding.embed_texts.call_count, 0)
        self.assertEqual(mock_vector_store.store_chunks.call_count, 0)

    def test_dry_run_cli_execution(self) -> None:
        """Verify CLI dry run execution reports metrics without errors."""
        import io
        import contextlib

        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            execute_indexing_cli(["--dry-run"])

        output = stdout_buf.getvalue()
        self.assertIn("DRY RUN mode", output)
        self.assertIn("--- Dry Run Summary ---", output)
        self.assertIn("Documents processed:", output)
        self.assertIn("Chunks created:", output)
        self.assertIn("Embeddings generated: 0 (dry run)", output)
        self.assertIn("Vectors indexed:      0 (dry run)", output)
        self.assertIn("Failures:             0", output)

    def test_secret_sanitization(self) -> None:
        """Verify API keys and credentials are sanitized from errors and failure objects."""
        from app.services.indexing import sanitize_error_message

        dummy_gemini_key = "AIzaSyFakeTestTokenForSanitization12345"
        raw_err = f"Failed calling https://generativelanguage.googleapis.com with key={dummy_gemini_key} and api_key=dummy_test_secret_xyz"
        sanitized = sanitize_error_message(raw_err)
        self.assertNotIn(dummy_gemini_key, sanitized)
        self.assertNotIn("dummy_test_secret_xyz", sanitized)
        self.assertIn("[REDACTED", sanitized)

    async def test_gemini_embedding_service_mock_integration(self) -> None:
        """Verify GeminiEmbeddingService mock client produces 1536-dim vectors and integrates into indexing."""
        from google.genai import types
        from app.services.embedding import GeminiEmbeddingService

        mock_genai_client = MagicMock()
        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = [0.01] * 1536
        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding_obj]
        mock_genai_client.models.embed_content.return_value = mock_response

        gemini_service = GeminiEmbeddingService(
            api_key="mock-gemini-key",
            model="gemini-embedding-2",
            dimension=1536,
            client=mock_genai_client,
        )

        vec = gemini_service.embed_text("Sample query text")
        self.assertEqual(len(vec), 1536)
        self.assertEqual(vec[0], 0.01)

        vecs = gemini_service.embed_texts(["Sample chunk 1"])
        self.assertEqual(len(vecs), 1)
        self.assertEqual(len(vecs[0]), 1536)

    def test_indexing_result_model_properties(self) -> None:
        """Verify IndexingResult model fields, aliases, and properties."""
        res = IndexingResult(
            documents_discovered=3,
            documents_processed=3,
            chunks_created=10,
            embeddings_generated=10,
            vectors_upserted=10,
            point_ids=["p1", "p2"],
        )
        self.assertEqual(res.documents_discovered, 3)
        self.assertEqual(res.documents_processed, 3)
        self.assertEqual(res.chunks_created, 10)
        self.assertEqual(res.embeddings_generated, 10)
        self.assertEqual(res.vectors_upserted, 10)
        self.assertEqual(res.vectors_indexed, 10)
        self.assertEqual(res.chunks_indexed, 10)
        self.assertTrue(res.is_success)
        self.assertFalse(res.has_failures)


if __name__ == "__main__":
    unittest.main()

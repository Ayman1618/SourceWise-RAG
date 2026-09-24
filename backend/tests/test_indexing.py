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
    IndexingError,
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


if __name__ == "__main__":
    unittest.main()

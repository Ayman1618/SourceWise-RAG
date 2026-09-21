"""Unit tests for vector store service and Qdrant implementation."""

import unittest
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.models.chunk import Chunk
from app.services.vector_store import BaseVectorStoreService, QdrantVectorStoreService


class TestVectorStoreService(unittest.TestCase):
    """Test suite for vector store contracts and Qdrant service implementation."""

    def setUp(self) -> None:
        """Create sample chunks and vectors for testing."""
        self.sample_chunk_1 = Chunk(
            chunk_id="doc_runbook#chunk_0",
            document_id="doc_runbook",
            text="First chunk content for RAG indexing.",
            chunk_index=0,
            token_count=8,
            metadata={
                "title": "Incident Runbook",
                "filepath": "/docs/runbook.md",
                "tags": ["ops", "production"],
            },
        )
        self.sample_chunk_2 = Chunk(
            chunk_id="doc_runbook#chunk_1",
            document_id="doc_runbook",
            text="Second chunk content with triage steps.",
            chunk_index=1,
            token_count=7,
            metadata={
                "title": "Incident Runbook",
                "filepath": "/docs/runbook.md",
                "tags": ["ops", "production"],
            },
        )
        self.sample_vectors = [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8],
        ]

    def test_base_vector_store_service_cannot_be_instantiated(self) -> None:
        """Verify abstract base class enforces method implementation."""
        with self.assertRaises(TypeError):
            BaseVectorStoreService()  # type: ignore[abstract]

    def test_concrete_mock_subclass(self) -> None:
        """Verify BaseVectorStoreService can be cleanly subclassed."""

        class MockVectorStore(BaseVectorStoreService):
            def connect(self) -> Any:
                return "connected"

            def collection_exists(self, collection_name: str | None = None) -> bool:
                return True

            def create_collection_if_not_exists(
                self,
                collection_name: str | None = None,
                vector_size: int | None = None,
                distance: str | None = None,
            ) -> bool:
                return True

            def store_chunks(
                self,
                chunks: list[Chunk],
                vectors: list[list[float]],
                collection_name: str | None = None,
            ) -> list[str]:
                return [f"id_{c.chunk_id}" for c in chunks]

            def close(self) -> None:
                pass

        service = MockVectorStore()
        self.assertIsInstance(service, BaseVectorStoreService)
        self.assertEqual(service.connect(), "connected")
        self.assertTrue(service.collection_exists())
        self.assertTrue(service.create_collection_if_not_exists())
        self.assertEqual(
            service.store_chunks([self.sample_chunk_1], [[0.1]]),
            ["id_doc_runbook#chunk_0"],
        )

    def test_qdrant_service_defaults(self) -> None:
        """Verify Qdrant service initializes with backend settings defaults."""
        mock_client = MagicMock()
        service = QdrantVectorStoreService(client=mock_client)

        self.assertEqual(service.url, settings.qdrant_url)
        self.assertEqual(service.api_key, settings.qdrant_api_key)
        self.assertEqual(service.collection_name, settings.qdrant_collection_name)
        self.assertEqual(service.vector_size, settings.qdrant_vector_size)
        self.assertEqual(service.distance_str, settings.qdrant_distance)
        self.assertEqual(service.timeout, settings.qdrant_timeout)
        self.assertEqual(service.connect(), mock_client)

    def test_qdrant_service_custom_config(self) -> None:
        """Verify Qdrant service accepts custom parameter overrides."""
        mock_client = MagicMock()
        service = QdrantVectorStoreService(
            url="http://custom-qdrant:6333",
            api_key="secret-api-key",
            collection_name="custom_collection",
            vector_size=768,
            distance="Dot",
            timeout=20.0,
            client=mock_client,
        )

        self.assertEqual(service.url, "http://custom-qdrant:6333")
        self.assertEqual(service.api_key, "secret-api-key")
        self.assertEqual(service.collection_name, "custom_collection")
        self.assertEqual(service.vector_size, 768)
        self.assertEqual(service.distance_str, "Dot")
        self.assertEqual(service.timeout, 20.0)

    def test_chunk_id_to_point_id_deterministic(self) -> None:
        """Verify chunk_id_to_point_id generates valid, deterministic UUIDv5 strings."""
        chunk_id = "doc_test#chunk_42"
        point_id_1 = QdrantVectorStoreService.chunk_id_to_point_id(chunk_id)
        point_id_2 = QdrantVectorStoreService.chunk_id_to_point_id(chunk_id)

        # Must be valid UUID
        parsed_uuid = UUID(point_id_1)
        self.assertEqual(parsed_uuid.version, 5)

        # Must be deterministic for same chunk_id
        self.assertEqual(point_id_1, point_id_2)

        # Distinct chunk_ids produce distinct point IDs
        other_point_id = QdrantVectorStoreService.chunk_id_to_point_id("doc_test#chunk_43")
        self.assertNotEqual(point_id_1, other_point_id)

    def test_collection_exists(self) -> None:
        """Verify collection_exists delegates to Qdrant client."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True

        service = QdrantVectorStoreService(client=mock_client, collection_name="docs_col")
        self.assertTrue(service.collection_exists())
        mock_client.collection_exists.assert_called_once_with(collection_name="docs_col")

        mock_client.collection_exists.return_value = False
        self.assertFalse(service.collection_exists("other_col"))
        mock_client.collection_exists.assert_called_with(collection_name="other_col")

    def test_create_collection_if_not_exists_when_already_exists(self) -> None:
        """Verify create_collection_if_not_exists skips creation if collection exists."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True

        service = QdrantVectorStoreService(client=mock_client)
        created = service.create_collection_if_not_exists("existing_col")

        self.assertFalse(created)
        mock_client.create_collection.assert_not_called()

    def test_create_collection_if_not_exists_when_absent(self) -> None:
        """Verify create_collection_if_not_exists creates collection with correct VectorParams."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False

        service = QdrantVectorStoreService(
            client=mock_client,
            collection_name="new_col",
            vector_size=1536,
            distance="Cosine",
        )
        created = service.create_collection_if_not_exists()

        self.assertTrue(created)
        mock_client.create_collection.assert_called_once_with(
            collection_name="new_col",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    def test_create_collection_with_unsupported_distance_raises(self) -> None:
        """Verify invalid distance string raises ValueError."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False

        service = QdrantVectorStoreService(client=mock_client)
        with self.assertRaises(ValueError) as ctx:
            service.create_collection_if_not_exists(distance="Manhattan")
        self.assertIn("Unsupported distance metric", str(ctx.exception))

    def test_build_payload_preserves_provenance(self) -> None:
        """Verify payload schema preserves chunk_id -> document_id -> metadata."""
        service = QdrantVectorStoreService(client=MagicMock())
        payload = service.build_payload(self.sample_chunk_1)

        expected_payload = {
            "chunk_id": "doc_runbook#chunk_0",
            "document_id": "doc_runbook",
            "text": "First chunk content for RAG indexing.",
            "chunk_index": 0,
            "token_count": 8,
            "metadata": {
                "title": "Incident Runbook",
                "filepath": "/docs/runbook.md",
                "tags": ["ops", "production"],
            },
        }
        self.assertEqual(payload, expected_payload)

    def test_store_chunks_empty_inputs(self) -> None:
        """Verify store_chunks returns empty list when given no chunks or vectors."""
        mock_client = MagicMock()
        service = QdrantVectorStoreService(client=mock_client)

        result = service.store_chunks([], [])
        self.assertEqual(result, [])
        mock_client.upsert.assert_not_called()

    def test_store_chunks_mismatched_lengths_raises(self) -> None:
        """Verify store_chunks raises ValueError when chunks and vectors count differ."""
        mock_client = MagicMock()
        service = QdrantVectorStoreService(client=mock_client)

        with self.assertRaises(ValueError) as ctx:
            service.store_chunks([self.sample_chunk_1], [[0.1], [0.2]])
        self.assertIn("Mismatch", str(ctx.exception))

    def test_store_chunks_empty_vector_raises(self) -> None:
        """Verify store_chunks raises ValueError if a vector is empty."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        service = QdrantVectorStoreService(client=mock_client)

        with self.assertRaises(ValueError) as ctx:
            service.store_chunks([self.sample_chunk_1], [[]])
        self.assertIn("is empty", str(ctx.exception))

    def test_store_chunks_mocked_upsert(self) -> None:
        """Verify store_chunks creates collection if absent and upserts PointStruct records."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = False

        service = QdrantVectorStoreService(client=mock_client, collection_name="test_col")
        chunks = [self.sample_chunk_1, self.sample_chunk_2]
        vectors = self.sample_vectors

        point_ids = service.store_chunks(chunks, vectors)

        self.assertEqual(len(point_ids), 2)
        self.assertEqual(point_ids[0], service.chunk_id_to_point_id("doc_runbook#chunk_0"))
        self.assertEqual(point_ids[1], service.chunk_id_to_point_id("doc_runbook#chunk_1"))

        # Collection creation should have been invoked with vector dimension 4
        mock_client.create_collection.assert_called_once_with(
            collection_name="test_col",
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )

        # Upsert should have been invoked with PointStruct instances
        mock_client.upsert.assert_called_once()
        call_kwargs = mock_client.upsert.call_args[1]
        self.assertEqual(call_kwargs["collection_name"], "test_col")

        points = call_kwargs["points"]
        self.assertEqual(len(points), 2)
        self.assertIsInstance(points[0], PointStruct)
        self.assertEqual(points[0].id, point_ids[0])
        self.assertEqual(points[0].vector, [0.1, 0.2, 0.3, 0.4])
        self.assertEqual(points[0].payload["chunk_id"], "doc_runbook#chunk_0")
        self.assertEqual(points[0].payload["document_id"], "doc_runbook")
        self.assertEqual(points[0].payload["metadata"]["filepath"], "/docs/runbook.md")

    def test_close(self) -> None:
        """Verify close method closes client connection."""
        mock_client = MagicMock()
        service = QdrantVectorStoreService(client=mock_client)

        service.close()
        mock_client.close.assert_called_once()
        self.assertIsNone(service._client)

    def test_in_memory_qdrant_integration(self) -> None:
        """Verify full workflow using offline in-memory Qdrant instance."""
        in_memory_client = QdrantClient(":memory:")
        service = QdrantVectorStoreService(
            client=in_memory_client,
            collection_name="in_memory_docs",
            vector_size=4,
        )

        chunks = [self.sample_chunk_1, self.sample_chunk_2]
        point_ids = service.store_chunks(chunks, self.sample_vectors)

        self.assertEqual(len(point_ids), 2)
        self.assertTrue(service.collection_exists("in_memory_docs"))

        # Retrieve stored points from in-memory Qdrant and verify payload lineage
        retrieved_points = in_memory_client.retrieve(
            collection_name="in_memory_docs",
            ids=point_ids,
            with_payload=True,
            with_vectors=True,
        )

        self.assertEqual(len(retrieved_points), 2)
        retrieved_map = {p.id: p for p in retrieved_points}

        # Check chunk 1 lineage
        p1 = retrieved_map[point_ids[0]]
        self.assertEqual(p1.payload["chunk_id"], "doc_runbook#chunk_0")
        self.assertEqual(p1.payload["document_id"], "doc_runbook")
        self.assertEqual(p1.payload["text"], "First chunk content for RAG indexing.")
        self.assertEqual(p1.payload["metadata"]["title"], "Incident Runbook")
        self.assertEqual(len(p1.vector), 4)

        # Check chunk 2 lineage
        p2 = retrieved_map[point_ids[1]]
        self.assertEqual(p2.payload["chunk_id"], "doc_runbook#chunk_1")
        self.assertEqual(p2.payload["document_id"], "doc_runbook")
        self.assertEqual(p2.payload["metadata"]["tags"], ["ops", "production"])
        self.assertEqual(len(p2.vector), 4)



if __name__ == "__main__":
    unittest.main()

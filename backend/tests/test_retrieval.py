"""Unit and integration tests for semantic retrieval service with Qdrant."""

import unittest
from unittest.mock import MagicMock

from qdrant_client import QdrantClient

from app.models.chunk import Chunk
from app.models.retrieval import RetrievalQuery, RetrievedChunk
from app.services.embedding import BaseEmbeddingService
from app.services.retrieval import BaseRetrievalService, QdrantRetrievalService
from app.services.vector_store import (
    BaseVectorStoreService,
    QdrantVectorStoreService,
    VectorSearchResult,
)


class TestRetrievalService(unittest.IsolatedAsyncioTestCase):
    """Test suite for BaseRetrievalService contracts and QdrantRetrievalService implementation."""


    def setUp(self) -> None:
        """Set up test fixtures with sample chunks and results."""
        self.sample_chunk_1 = Chunk(
            chunk_id="doc_auth#chunk_0",
            document_id="doc_auth",
            text="OAuth2 authentication setup and JWT token configuration.",
            chunk_index=0,
            token_count=10,
            metadata={
                "title": "Auth Architecture",
                "product": "sourcewise-rag",
                "department": "security",
                "version": "1.0",
            },
        )
        self.sample_chunk_2 = Chunk(
            chunk_id="doc_auth#chunk_1",
            document_id="doc_auth",
            text="RBAC role definitions and permission mapping for enterprise users.",
            chunk_index=1,
            token_count=12,
            metadata={
                "title": "Auth Architecture",
                "product": "sourcewise-rag",
                "department": "security",
                "version": "1.0",
            },
        )
        self.sample_chunk_3 = Chunk(
            chunk_id="doc_billing#chunk_0",
            document_id="doc_billing",
            text="Stripe webhook processing and invoice generation procedures.",
            chunk_index=0,
            token_count=9,
            metadata={
                "title": "Billing System",
                "product": "billing-core",
                "department": "finance",
                "version": "2.0",
            },
        )

    def test_base_retrieval_service_cannot_be_instantiated(self) -> None:
        """Verify abstract base class enforces retrieve implementation."""
        with self.assertRaises(TypeError):
            BaseRetrievalService()  # type: ignore[abstract]

    def test_concrete_mock_subclass(self) -> None:
        """Verify BaseRetrievalService can be subclassed cleanly."""

        class MockRetrieval(BaseRetrievalService):
            async def retrieve(
                self,
                query: str | RetrievalQuery,
                top_k: int = 5,
                filters: dict | None = None,
                **kwargs,
            ) -> list[RetrievedChunk]:
                return [
                    RetrievedChunk(
                        chunk=self.sample_chunk_1,
                        score=0.95,
                        rank=1,
                        retrieval_method="dense",
                    )
                ]

        service = MockRetrieval()
        self.assertIsInstance(service, BaseRetrievalService)

    async def test_qdrant_retrieval_flow_mocked(self) -> None:
        """Verify the full retrieval flow: Query -> Embedding -> VectorStore -> RetrievedChunks."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.query_embedding.return_value = [0.1, 0.2, 0.3, 0.4]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.search.return_value = [
            VectorSearchResult(chunk=self.sample_chunk_1, score=0.92),
            VectorSearchResult(chunk=self.sample_chunk_2, score=0.85),
        ]

        service = QdrantRetrievalService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        results = await service.retrieve(
            query="how to configure oauth2 tokens",
            top_k=2,
            filters={"department": "security"},
            score_threshold=0.8,
        )

        # 1. Verify query embedding was generated
        mock_embedding.query_embedding.assert_called_once_with("how to configure oauth2 tokens")

        # 2. Verify vector store search was called with correct parameters
        mock_vector_store.search.assert_called_once_with(
            vector=[0.1, 0.2, 0.3, 0.4],
            top_k=2,
            filters={"department": "security"},
            score_threshold=0.8,
        )

        # 3. Verify results conversion to RetrievedChunk
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], RetrievedChunk)
        self.assertIsInstance(results[1], RetrievedChunk)

        # 4. Verify ranks are 1-indexed
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[1].rank, 2)

        # 5. Verify scores preserved
        self.assertEqual(results[0].score, 0.92)
        self.assertEqual(results[1].score, 0.85)

        # 6. Verify chunk provenance preserved
        self.assertEqual(results[0].chunk_id, "doc_auth#chunk_0")
        self.assertEqual(results[0].document_id, "doc_auth")
        self.assertEqual(results[0].text, self.sample_chunk_1.text)
        self.assertEqual(results[0].chunk.metadata["product"], "sourcewise-rag")
        self.assertEqual(results[0].retrieval_method, "dense")

    async def test_retrieve_with_retrieval_query_model(self) -> None:
        """Verify retrieve accepts a structured RetrievalQuery model instance."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.query_embedding.return_value = [0.5, 0.5]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.search.return_value = [
            VectorSearchResult(chunk=self.sample_chunk_3, score=0.88)
        ]

        service = QdrantRetrievalService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        query_obj = RetrievalQuery(
            query="stripe billing webhooks",
            top_k=3,
            filters={"product": "billing-core"},
        )

        results = await service.retrieve(query=query_obj)

        mock_embedding.query_embedding.assert_called_once_with("stripe billing webhooks")
        mock_vector_store.search.assert_called_once_with(
            vector=[0.5, 0.5],
            top_k=3,
            filters={"product": "billing-core"},
            score_threshold=None,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc_billing")
        self.assertEqual(results[0].rank, 1)

    async def test_empty_results_handled(self) -> None:
        """Verify empty vector store results return an empty list."""
        mock_embedding = MagicMock(spec=BaseEmbeddingService)
        mock_embedding.query_embedding.return_value = [0.1, 0.1]

        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.search.return_value = []

        service = QdrantRetrievalService(
            embedding_service=mock_embedding,
            vector_store_service=mock_vector_store,
        )

        results = await service.retrieve("unrelated query")
        self.assertEqual(results, [])

    async def test_invalid_queries_raise_value_error(self) -> None:
        """Verify blank or invalid query types raise ValueError."""
        service = QdrantRetrievalService(
            embedding_service=MagicMock(),
            vector_store_service=MagicMock(),
        )

        # Empty string
        with self.assertRaises(ValueError) as ctx:
            await service.retrieve("")
        self.assertIn("cannot be empty", str(ctx.exception))

        # Whitespace only
        with self.assertRaises(ValueError) as ctx:
            await service.retrieve("   \n\t  ")
        self.assertIn("cannot be empty", str(ctx.exception))

        # Invalid type
        with self.assertRaises(ValueError) as ctx:
            await service.retrieve(12345)  # type: ignore[arg-type]
        self.assertIn("Unsupported query type", str(ctx.exception))

    async def test_invalid_top_k_raises_value_error(self) -> None:
        """Verify top_k bounds validation (< 1, > 100, non-integer)."""
        service = QdrantRetrievalService(
            embedding_service=MagicMock(),
            vector_store_service=MagicMock(),
        )

        with self.assertRaises(ValueError) as ctx:
            await service.retrieve("query", top_k=0)
        self.assertIn("top_k must be an integer between 1 and 100", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            await service.retrieve("query", top_k=-5)
        self.assertIn("top_k must be an integer between 1 and 100", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            await service.retrieve("query", top_k=101)
        self.assertIn("top_k must be an integer between 1 and 100", str(ctx.exception))

    async def test_in_memory_qdrant_retrieval_integration(self) -> None:
        """Integration test verifying end-to-end flow with in-memory Qdrant and embedding stub."""
        in_memory_client = QdrantClient(":memory:")
        vector_store = QdrantVectorStoreService(
            client=in_memory_client,
            collection_name="test_retrieval_collection",
            vector_size=3,
        )

        # 3 orthogonal vectors for 3 chunks
        chunks = [self.sample_chunk_1, self.sample_chunk_2, self.sample_chunk_3]
        vectors = [
            [1.0, 0.0, 0.0],  # auth chunk 0
            [0.8, 0.2, 0.0],  # auth chunk 1
            [0.0, 0.0, 1.0],  # billing chunk 0
        ]
        vector_store.store_chunks(chunks=chunks, vectors=vectors)

        # Mock embedding service to return a vector close to auth
        class StubEmbeddingService(BaseEmbeddingService):
            def embed_text(self, text: str) -> list[float]:
                return [1.0, 0.0, 0.0]

            def embed_texts(self, texts: list[str]) -> list[list[float]]:
                return [[1.0, 0.0, 0.0] for _ in texts]

            def query_embedding(self, query: str) -> list[float]:
                if "billing" in query.lower():
                    return [0.0, 0.0, 1.0]
                return [1.0, 0.0, 0.0]

        retrieval_service = QdrantRetrievalService(
            embedding_service=StubEmbeddingService(),
            vector_store_service=vector_store,
        )

        # 1. Unfiltered query matching auth
        results = await retrieval_service.retrieve(
            query="how does authentication work?",
            top_k=2,
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[0].chunk_id, "doc_auth#chunk_0")
        self.assertEqual(results[1].rank, 2)
        self.assertEqual(results[1].chunk_id, "doc_auth#chunk_1")

        # 2. Query matching billing
        billing_results = await retrieval_service.retrieve(
            query="billing invoice setup",
            top_k=1,
        )
        self.assertEqual(len(billing_results), 1)
        self.assertEqual(billing_results[0].chunk_id, "doc_billing#chunk_0")
        self.assertEqual(billing_results[0].document_id, "doc_billing")

        # 3. Filtered retrieval by department
        filtered_results = await retrieval_service.retrieve(
            query="security procedures",
            top_k=5,
            filters={"department": "security"},
        )
        self.assertEqual(len(filtered_results), 2)
        for r in filtered_results:
            self.assertEqual(r.chunk.metadata["department"], "security")

        # 4. Filtered retrieval by document_id
        doc_filtered_results = await retrieval_service.retrieve(
            query="information",
            top_k=5,
            filters={"document_id": "doc_billing"},
        )
        self.assertEqual(len(doc_filtered_results), 1)
        self.assertEqual(doc_filtered_results[0].document_id, "doc_billing")


if __name__ == "__main__":
    unittest.main()

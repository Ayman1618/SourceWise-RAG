"""Integration and unit tests for FastAPI POST /api/v1/query endpoint."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import (
    get_generation_service,
    get_query_orchestration_service,
    get_retrieval_service,
)
from app.main import app
from app.models.chunk import Chunk
from app.models.citation import Citation
from app.models.generation import Answer, EvidenceStatus
from app.models.retrieval import RetrievedChunk
from app.services.generation import BaseGenerationService
from app.services.query import BaseQueryOrchestrationService, QueryOrchestrationService
from app.services.retrieval import BaseRetrievalService


class TestQueryAPI(unittest.TestCase):
    """Test suite for /api/v1/query endpoint."""

    def setUp(self) -> None:
        """Configure test client and mock dependencies."""
        self.client = TestClient(app)

        self.mock_retrieval_service = MagicMock(spec=BaseRetrievalService)
        self.mock_retrieval_service.retrieve = AsyncMock()

        self.mock_generation_service = MagicMock(spec=BaseGenerationService)
        self.mock_generation_service.generate = AsyncMock()

        self.sample_chunk = Chunk(
            chunk_id="doc_kb_1#chunk_0",
            document_id="doc_kb_1",
            text="Passage text explaining how to reset user credentials.",
            chunk_index=0,
            metadata={"title": "Credential Management"},
        )
        self.sample_retrieved = RetrievedChunk(
            chunk=self.sample_chunk,
            score=0.91,
            rank=1,
            retrieval_method="dense",
        )
        self.sample_citation = Citation(
            citation_id="cite_1",
            document_id="doc_kb_1",
            chunk_id="doc_kb_1#chunk_0",
            source_title="Credential Management",
            passage="Passage text explaining how to reset user credentials.",
            score=0.91,
        )
        self.sample_answer = Answer(
            query="How do I reset credentials?",
            answer="To reset credentials, follow the credential management runbook [cite_1].",
            citations=[self.sample_citation],
            evidence=[self.sample_retrieved],
            evidence_status=EvidenceStatus.SUFFICIENT,
            has_sufficient_evidence=True,
            confidence_score=0.91,
        )

    def tearDown(self) -> None:
        """Clear dependency overrides after test run."""
        app.dependency_overrides.clear()

    def test_successful_query_end_to_end_with_dependencies(self) -> None:
        """Verify successful 200 OK query returning grounded answer."""
        self.mock_retrieval_service.retrieve.return_value = [self.sample_retrieved]
        self.mock_generation_service.generate.return_value = self.sample_answer

        app.dependency_overrides[get_retrieval_service] = lambda: self.mock_retrieval_service
        app.dependency_overrides[get_generation_service] = lambda: self.mock_generation_service

        payload = {
            "query": "How do I reset credentials?",
            "top_k": 5,
        }
        response = self.client.post("/api/v1/query", json=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["query"], "How do I reset credentials?")
        self.assertEqual(data["answer"], self.sample_answer.answer)
        self.assertEqual(data["evidence_status"], "sufficient")
        self.assertTrue(data["has_sufficient_evidence"])
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0]["chunk_id"], "doc_kb_1#chunk_0")
        self.assertEqual(data["citations"][0]["document_id"], "doc_kb_1")
        self.assertEqual(len(data["evidence"]), 1)

    def test_query_with_metadata_filters_and_top_k_propagation(self) -> None:
        """Verify top_k and metadata filters propagate to the orchestration service."""
        mock_orchestration = MagicMock(spec=BaseQueryOrchestrationService)
        mock_orchestration.query = AsyncMock(return_value=self.sample_answer)

        app.dependency_overrides[get_query_orchestration_service] = lambda: mock_orchestration

        payload = {
            "query": "How do I reset credentials?",
            "top_k": 8,
            "filters": {"department": "security", "product": "SourceWise"},
        }
        response = self.client.post("/api/v1/query", json=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_orchestration.query.assert_awaited_once()
        called_kwargs = mock_orchestration.query.call_args.kwargs
        self.assertEqual(called_kwargs["top_k"], 8)
        self.assertEqual(called_kwargs["filters"], {"department": "security", "product": "SourceWise"})

    def test_insufficient_evidence_response(self) -> None:
        """Verify API response preserves refusal and insufficient evidence status."""
        insufficient_answer = Answer(
            query="What is the internal company secret?",
            answer="I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
            citations=[],
            evidence=[],
            evidence_status=EvidenceStatus.INSUFFICIENT,
            has_sufficient_evidence=False,
            confidence_score=0.0,
        )

        mock_orchestration = MagicMock(spec=BaseQueryOrchestrationService)
        mock_orchestration.query = AsyncMock(return_value=insufficient_answer)

        app.dependency_overrides[get_query_orchestration_service] = lambda: mock_orchestration

        payload = {"query": "What is the internal company secret?"}
        response = self.client.post("/api/v1/query", json=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["evidence_status"], "insufficient")
        self.assertFalse(data["has_sufficient_evidence"])
        self.assertEqual(data["citations"], [])
        self.assertIn("couldn't find sufficient supporting information", data["answer"])

    def test_empty_query_rejected(self) -> None:
        """Verify empty query returns 422 or 400 Bad Request."""
        payload = {"query": ""}
        response = self.client.post("/api/v1/query", json=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_whitespace_query_rejected(self) -> None:
        """Verify whitespace query returns 422 validation failure."""
        payload = {"query": "   \n\t   "}
        response = self.client.post("/api/v1/query", json=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_oversized_query_rejected(self) -> None:
        """Verify query exceeding 1000 characters returns 422."""
        payload = {"query": "a" * 1001}
        response = self.client.post("/api/v1/query", json=payload)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_retrieval_failure_handled(self) -> None:
        """Verify retrieval service exception returns 500 without leaking stack traces or secrets."""
        self.mock_retrieval_service.retrieve.side_effect = RuntimeError("Qdrant connection error to https://secret-url.qdrant.tech:6333 with key=sk-12345")
        self.mock_generation_service.generate.return_value = self.sample_answer

        app.dependency_overrides[get_retrieval_service] = lambda: self.mock_retrieval_service
        app.dependency_overrides[get_generation_service] = lambda: self.mock_generation_service

        payload = {"query": "How do I troubleshoot login failures?"}
        response = self.client.post("/api/v1/query", json=payload)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.json()
        self.assertEqual(data["detail"], "An error occurred while processing the query. Please try again later.")
        # Ensure secret wasn't leaked
        self.assertNotIn("sk-12345", response.text)
        self.assertNotIn("secret-url", response.text)

    def test_generation_failure_handled(self) -> None:
        """Verify generation service failure returns 500 without leaking stack traces."""
        self.mock_retrieval_service.retrieve.return_value = [self.sample_retrieved]
        self.mock_generation_service.generate.side_effect = Exception("OpenAI API key sk-proj-supersecret invalid")

        app.dependency_overrides[get_retrieval_service] = lambda: self.mock_retrieval_service
        app.dependency_overrides[get_generation_service] = lambda: self.mock_generation_service

        payload = {"query": "How do I troubleshoot login failures?"}
        response = self.client.post("/api/v1/query", json=payload)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.json()
        self.assertEqual(data["detail"], "An error occurred while processing the query. Please try again later.")
        self.assertNotIn("sk-proj", response.text)

    def test_openapi_documentation_schema(self) -> None:
        """Verify OpenAPI schema publishes /api/v1/query with correct request and response schemas."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        openapi_data = response.json()

        paths = openapi_data.get("paths", {})
        self.assertIn("/api/v1/query", paths)

        query_post = paths["/api/v1/query"].get("post", {})
        self.assertEqual(query_post.get("summary"), "Execute grounded enterprise RAG query")
        self.assertIn("200", query_post.get("responses", {}))
        self.assertIn("422", query_post.get("responses", {}))
        self.assertIn("500", query_post.get("responses", {}))


if __name__ == "__main__":
    unittest.main()

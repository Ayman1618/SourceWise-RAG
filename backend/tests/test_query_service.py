"""Unit tests for QueryOrchestrationService."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from app.models.chunk import Chunk
from app.models.citation import Citation
from app.models.generation import Answer, EvidenceStatus
from app.models.query import QueryRequest
from app.models.retrieval import RetrievalQuery, RetrievedChunk
from app.services.generation import BaseGenerationService
from app.services.query import QueryOrchestrationService
from app.services.retrieval import BaseRetrievalService


class TestQueryOrchestrationService(unittest.IsolatedAsyncioTestCase):
    """Test suite for application-level query orchestration service."""

    def setUp(self) -> None:
        """Set up mock retrieval and generation services."""
        self.mock_retrieval_service = MagicMock(spec=BaseRetrievalService)
        self.mock_retrieval_service.retrieve = AsyncMock()

        self.mock_generation_service = MagicMock(spec=BaseGenerationService)
        self.mock_generation_service.generate = AsyncMock()

        self.orchestration_service = QueryOrchestrationService(
            retrieval_service=self.mock_retrieval_service,
            generation_service=self.mock_generation_service,
        )

        self.sample_chunk = Chunk(
            chunk_id="doc_kb_1#chunk_0",
            document_id="doc_kb_1",
            text="To resolve error 503, restart the background worker service.",
            chunk_index=0,
            metadata={"title": "Error Troubleshooting Guide"},
        )
        self.sample_retrieved = RetrievedChunk(
            chunk=self.sample_chunk,
            score=0.92,
            rank=1,
            retrieval_method="dense",
        )
        self.sample_citation = Citation(
            citation_id="cite_1",
            document_id="doc_kb_1",
            chunk_id="doc_kb_1#chunk_0",
            source_title="Error Troubleshooting Guide",
            passage="To resolve error 503, restart the background worker service.",
            score=0.92,
        )
        self.sample_answer = Answer(
            query="How to fix error 503?",
            answer="Restart the background worker service to resolve error 503.",
            citations=[self.sample_citation],
            evidence=[self.sample_retrieved],
            evidence_status=EvidenceStatus.SUFFICIENT,
            has_sufficient_evidence=True,
            confidence_score=0.92,
        )

    def test_default_service_initialization(self) -> None:
        """Verify QueryOrchestrationService can be initialized with defaults."""
        service = QueryOrchestrationService()
        self.assertIsNotNone(service.retrieval_service)
        self.assertIsNotNone(service.generation_service)

    async def test_successful_query_flow_with_string(self) -> None:
        """Verify successful query orchestration with string input."""
        self.mock_retrieval_service.retrieve.return_value = [self.sample_retrieved]
        self.mock_generation_service.generate.return_value = self.sample_answer

        result = await self.orchestration_service.query(
            query="How to fix error 503?",
            top_k=5,
        )

        self.assertEqual(result, self.sample_answer)
        self.mock_retrieval_service.retrieve.assert_awaited_once_with(
            query="How to fix error 503?",
            top_k=5,
            filters=None,
        )
        self.mock_generation_service.generate.assert_awaited_once_with(
            query="How to fix error 503?",
            evidence=[self.sample_retrieved],
        )

    async def test_successful_query_flow_with_query_request(self) -> None:
        """Verify orchestration with QueryRequest model object."""
        self.mock_retrieval_service.retrieve.return_value = [self.sample_retrieved]
        self.mock_generation_service.generate.return_value = self.sample_answer

        request = QueryRequest(
            query="  How to fix error 503?  ",
            top_k=10,
            filters={"department": "it"},
        )
        result = await self.orchestration_service.query(query=request)

        self.assertEqual(result, self.sample_answer)
        self.mock_retrieval_service.retrieve.assert_awaited_once_with(
            query="How to fix error 503?",
            top_k=10,
            filters={"department": "it"},
        )
        self.mock_generation_service.generate.assert_awaited_once_with(
            query="How to fix error 503?",
            evidence=[self.sample_retrieved],
        )

    async def test_successful_query_flow_with_retrieval_query(self) -> None:
        """Verify orchestration with RetrievalQuery model object."""
        self.mock_retrieval_service.retrieve.return_value = [self.sample_retrieved]
        self.mock_generation_service.generate.return_value = self.sample_answer

        retrieval_q = RetrievalQuery(
            query="How to fix error 503?",
            top_k=8,
            filters={"env": "prod"},
        )
        result = await self.orchestration_service.query(query=retrieval_q)

        self.assertEqual(result, self.sample_answer)
        self.mock_retrieval_service.retrieve.assert_awaited_once_with(
            query="How to fix error 503?",
            top_k=8,
            filters={"env": "prod"},
        )

    async def test_empty_or_whitespace_query_rejection(self) -> None:
        """Verify that empty or whitespace strings raise ValueError."""
        with self.assertRaises(ValueError):
            await self.orchestration_service.query(query="")

        with self.assertRaises(ValueError):
            await self.orchestration_service.query(query="   \t\n  ")

        with self.assertRaises(ValueError):
            await self.orchestration_service.query(query=12345)  # type: ignore[arg-type]

    async def test_retrieval_output_passed_accurately_to_generation(self) -> None:
        """Prove that retrieval chunks are passed directly into generation."""
        chunk2 = Chunk(
            chunk_id="doc_kb_1#chunk_1",
            document_id="doc_kb_1",
            text="Secondary note on service workers.",
            chunk_index=1,
        )
        retrieved2 = RetrievedChunk(chunk=chunk2, score=0.85, rank=2)
        chunks = [self.sample_retrieved, retrieved2]

        self.mock_retrieval_service.retrieve.return_value = chunks
        self.mock_generation_service.generate.return_value = self.sample_answer

        await self.orchestration_service.query(query="Test query")

        # Verify generation service received exact list of retrieved chunks
        called_args, called_kwargs = self.mock_generation_service.generate.call_args
        self.assertEqual(called_kwargs["evidence"], chunks)

    async def test_insufficient_evidence_flow(self) -> None:
        """Verify insufficient evidence answer is returned correctly."""
        insufficient_answer = Answer(
            query="Unknown obscure query",
            answer="I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
            citations=[],
            evidence=[],
            evidence_status=EvidenceStatus.INSUFFICIENT,
            has_sufficient_evidence=False,
            confidence_score=0.0,
        )
        self.mock_retrieval_service.retrieve.return_value = []
        self.mock_generation_service.generate.return_value = insufficient_answer

        result = await self.orchestration_service.query(query="Unknown obscure query")

        self.assertEqual(result.evidence_status, EvidenceStatus.INSUFFICIENT)
        self.assertFalse(result.has_sufficient_evidence)
        self.assertEqual(result.citations, [])

    async def test_retrieval_service_failure_propagation(self) -> None:
        """Verify retrieval service exceptions bubble up."""
        self.mock_retrieval_service.retrieve.side_effect = RuntimeError("Vector DB unreachable")

        with self.assertRaises(RuntimeError) as ctx:
            await self.orchestration_service.query(query="Test query")
        self.assertIn("Vector DB unreachable", str(ctx.exception))
        self.mock_generation_service.generate.assert_not_called()

    async def test_generation_service_failure_propagation(self) -> None:
        """Verify generation service exceptions bubble up."""
        self.mock_retrieval_service.retrieve.return_value = [self.sample_retrieved]
        self.mock_generation_service.generate.side_effect = RuntimeError("LLM API rate limit exceeded")

        with self.assertRaises(RuntimeError) as ctx:
            await self.orchestration_service.query(query="Test query")
        self.assertIn("LLM API rate limit exceeded", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

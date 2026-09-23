"""Unit and integration tests for grounded answer generation and citation synthesis."""

import json
import unittest
from unittest.mock import MagicMock

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.citation import Citation
from app.models.generation import Answer, EvidenceStatus
from app.models.retrieval import RetrievedChunk
from app.services.generation import BaseGenerationService, GroundedGenerationService


class TestGenerationService(unittest.IsolatedAsyncioTestCase):
    """Test suite for BaseGenerationService contracts and GroundedGenerationService implementation."""

    def setUp(self) -> None:
        """Set up test fixtures with sample retrieved chunks."""
        self.chunk_1 = Chunk(
            chunk_id="doc_postgres#chunk_0",
            document_id="doc_postgres",
            text="In case of primary node failure, run 'pg_ctl promote' on the replica node.",
            chunk_index=0,
            token_count=15,
            metadata={
                "title": "PostgreSQL Recovery Runbook",
                "source_path": "docs/ops/postgres_recovery.md",
                "department": "infrastructure",
            },
        )
        self.retrieved_chunk_1 = RetrievedChunk(
            chunk=self.chunk_1,
            score=0.94,
            rank=1,
            retrieval_method="dense",
        )

        self.chunk_2 = Chunk(
            chunk_id="doc_postgres#chunk_1",
            document_id="doc_postgres",
            text="After failover promotion, reconfigure application pool connection strings to point to the new primary.",
            chunk_index=1,
            token_count=18,
            metadata={
                "title": "PostgreSQL Recovery Runbook",
                "source_path": "docs/ops/postgres_recovery.md",
                "department": "infrastructure",
            },
        )
        self.retrieved_chunk_2 = RetrievedChunk(
            chunk=self.chunk_2,
            score=0.88,
            rank=2,
            retrieval_method="dense",
        )

    def test_base_generation_service_cannot_be_instantiated(self) -> None:
        """Verify abstract base class enforces generate implementation."""
        with self.assertRaises(TypeError):
            BaseGenerationService()  # type: ignore[abstract]

    def test_concrete_mock_subclass(self) -> None:
        """Verify BaseGenerationService can be subclassed cleanly."""

        class MockGeneration(BaseGenerationService):
            async def generate(
                self,
                query: str,
                evidence: list[RetrievedChunk],
                **kwargs,
            ) -> Answer:
                return Answer(
                    query=query,
                    answer="Sample answer",
                    citations=[],
                    evidence=evidence,
                )

        service = MockGeneration()
        self.assertIsInstance(service, BaseGenerationService)

    def test_initialization_defaults_and_custom_config(self) -> None:
        """Verify initialization with backend settings defaults and custom overrides."""
        mock_client = MagicMock()
        default_service = GroundedGenerationService(client=mock_client)

        self.assertEqual(default_service.model, settings.llm_model)
        self.assertEqual(default_service.temperature, settings.llm_temperature)
        self.assertEqual(default_service.max_tokens, settings.llm_max_tokens)
        self.assertEqual(default_service.min_evidence_score, settings.min_evidence_score)

        custom_service = GroundedGenerationService(
            model="custom-llm-model",
            temperature=0.7,
            max_tokens=512,
            min_evidence_score=0.5,
            client=mock_client,
        )
        self.assertEqual(custom_service.model, "custom-llm-model")
        self.assertEqual(custom_service.temperature, 0.7)
        self.assertEqual(custom_service.max_tokens, 512)
        self.assertEqual(custom_service.min_evidence_score, 0.5)

    async def test_blank_query_raises_value_error(self) -> None:
        """Verify generate rejects blank or whitespace queries."""
        service = GroundedGenerationService(client=MagicMock())

        with self.assertRaises(ValueError) as ctx:
            await service.generate(query="", evidence=[self.retrieved_chunk_1])
        self.assertIn("cannot be empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            await service.generate(query="   \n\t ", evidence=[self.retrieved_chunk_1])
        self.assertIn("cannot be empty", str(ctx.exception))

    async def test_zero_evidence_returns_immediate_refusal(self) -> None:
        """Verify zero retrieved evidence returns refusal without invoking LLM."""
        mock_client = MagicMock()
        service = GroundedGenerationService(client=mock_client)

        answer = await service.generate(
            query="How do I recover PostgreSQL?",
            evidence=[],
        )

        self.assertEqual(answer.answer, GroundedGenerationService.REFUSAL_MESSAGE)
        self.assertEqual(answer.citations, [])
        self.assertEqual(answer.evidence, [])
        self.assertEqual(answer.evidence_status, EvidenceStatus.INSUFFICIENT)
        self.assertFalse(answer.has_sufficient_evidence)
        self.assertEqual(answer.confidence_score, 0.0)
        mock_client.chat.completions.create.assert_not_called()

    async def test_low_score_evidence_filter_returns_refusal(self) -> None:
        """Verify that when min_evidence_score filters all chunks, refusal is returned."""
        mock_client = MagicMock()
        service = GroundedGenerationService(
            min_evidence_score=0.98,  # Higher than 0.94
            client=mock_client,
        )

        answer = await service.generate(
            query="How do I recover PostgreSQL?",
            evidence=[self.retrieved_chunk_1],
        )

        self.assertEqual(answer.answer, GroundedGenerationService.REFUSAL_MESSAGE)
        self.assertEqual(answer.evidence_status, EvidenceStatus.INSUFFICIENT)
        self.assertFalse(answer.has_sufficient_evidence)
        mock_client.chat.completions.create.assert_not_called()

    async def test_successful_grounded_answer_single_citation(self) -> None:
        """Verify successful grounded generation with citation linking to source chunk."""
        mock_client = MagicMock()
        llm_payload = {
            "has_sufficient_evidence": True,
            "answer": "To recover the primary node, execute 'pg_ctl promote' on the standby replica.",
            "citations": [
                {
                    "chunk_id": "doc_postgres#chunk_0",
                    "passage": "In case of primary node failure, run 'pg_ctl promote' on the replica node.",
                }
            ],
        }
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(llm_payload)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="How do I promote the PostgreSQL replica?",
            evidence=[self.retrieved_chunk_1],
        )

        self.assertEqual(
            answer.answer,
            "To recover the primary node, execute 'pg_ctl promote' on the standby replica.",
        )
        self.assertEqual(answer.evidence_status, EvidenceStatus.SUFFICIENT)
        self.assertTrue(answer.has_sufficient_evidence)
        self.assertEqual(len(answer.citations), 1)

        citation = answer.citations[0]
        self.assertEqual(citation.citation_id, "cite_1")
        self.assertEqual(citation.chunk_id, "doc_postgres#chunk_0")
        self.assertEqual(citation.document_id, "doc_postgres")
        self.assertEqual(citation.source_title, "PostgreSQL Recovery Runbook")
        self.assertEqual(citation.source_path, "docs/ops/postgres_recovery.md")
        self.assertEqual(citation.score, 0.94)

        mock_client.chat.completions.create.assert_called_once()

    async def test_multiple_citations_and_deduplication(self) -> None:
        """Verify multiple citations from different chunks and deduplication of duplicate cited chunk IDs."""
        mock_client = MagicMock()
        llm_payload = {
            "has_sufficient_evidence": True,
            "answer": "First promote the standby using 'pg_ctl promote', then reconfigure application connection strings.",
            "citations": [
                {
                    "chunk_id": "doc_postgres#chunk_0",
                    "passage": "run 'pg_ctl promote' on the replica node.",
                },
                {
                    "chunk_id": "doc_postgres#chunk_1",
                    "passage": "reconfigure application pool connection strings",
                },
                {
                    "chunk_id": "doc_postgres#chunk_0",  # Duplicate should be ignored
                    "passage": "duplicate mention",
                },
            ],
        }
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(llm_payload)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="What are the full failover steps?",
            evidence=[self.retrieved_chunk_1, self.retrieved_chunk_2],
        )

        self.assertEqual(len(answer.citations), 2)
        self.assertEqual(answer.citations[0].chunk_id, "doc_postgres#chunk_0")
        self.assertEqual(answer.citations[1].chunk_id, "doc_postgres#chunk_1")
        self.assertEqual(answer.citations[0].citation_id, "cite_1")
        self.assertEqual(answer.citations[1].citation_id, "cite_2")

    async def test_llm_reports_insufficient_evidence(self) -> None:
        """Verify that when LLM flags has_sufficient_evidence=False, refusal is returned with INSUFFICIENT status."""
        mock_client = MagicMock()
        llm_payload = {
            "has_sufficient_evidence": False,
            "answer": "I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
            "citations": [],
        }
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(llm_payload)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="What is the CEO's favorite food?",
            evidence=[self.retrieved_chunk_1],
        )

        self.assertEqual(answer.answer, GroundedGenerationService.REFUSAL_MESSAGE)
        self.assertEqual(answer.citations, [])
        self.assertEqual(answer.evidence_status, EvidenceStatus.INSUFFICIENT)
        self.assertFalse(answer.has_sufficient_evidence)

    async def test_hallucinated_citations_rejected_and_causes_refusal(self) -> None:
        """Verify that hallucinated citation IDs not matching evidence are rejected, causing REFUSED status."""
        mock_client = MagicMock()
        llm_payload = {
            "has_sufficient_evidence": True,
            "answer": "The server uses quantum encryption algorithms.",
            "citations": [
                {
                    "chunk_id": "doc_unrelated_fake#chunk_99",  # Hallucinated ID
                    "passage": "Quantum encryption details",
                }
            ],
        }
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(llm_payload)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="Does it use quantum encryption?",
            evidence=[self.retrieved_chunk_1],
        )

        # Because all citations were invalid/hallucinated, answer cannot be safely validated
        self.assertEqual(answer.answer, GroundedGenerationService.REFUSAL_MESSAGE)
        self.assertEqual(answer.citations, [])
        self.assertEqual(answer.evidence_status, EvidenceStatus.REFUSED)
        self.assertFalse(answer.has_sufficient_evidence)

    async def test_partial_valid_citations_retains_only_valid(self) -> None:
        """Verify that when one citation is valid and one is fake, only the valid one is kept."""
        mock_client = MagicMock()
        llm_payload = {
            "has_sufficient_evidence": True,
            "answer": "Execute 'pg_ctl promote' on the replica node.",
            "citations": [
                {
                    "chunk_id": "doc_postgres#chunk_0",  # Valid
                    "passage": "run 'pg_ctl promote' on the replica node.",
                },
                {
                    "chunk_id": "doc_fake#chunk_99",  # Fake
                    "passage": "fake statement",
                },
            ],
        }
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(llm_payload)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="How to promote?",
            evidence=[self.retrieved_chunk_1],
        )

        self.assertEqual(len(answer.citations), 1)
        self.assertEqual(answer.citations[0].chunk_id, "doc_postgres#chunk_0")
        self.assertEqual(answer.evidence_status, EvidenceStatus.SUFFICIENT)
        self.assertTrue(answer.has_sufficient_evidence)

    async def test_malformed_llm_json_refuses_safely(self) -> None:
        """Verify that malformed JSON from LLM results in safe refusal with REFUSED status."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Not valid JSON output from model"
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="Query",
            evidence=[self.retrieved_chunk_1],
        )

        self.assertEqual(answer.answer, GroundedGenerationService.REFUSAL_MESSAGE)
        self.assertEqual(answer.evidence_status, EvidenceStatus.REFUSED)
        self.assertFalse(answer.has_sufficient_evidence)

    async def test_llm_api_failure_raises_exception(self) -> None:
        """Verify that client/network exceptions during LLM call are propagated."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("OpenAI API connection failed")

        service = GroundedGenerationService(client=mock_client)
        with self.assertRaises(RuntimeError) as ctx:
            await service.generate(query="Query", evidence=[self.retrieved_chunk_1])
        self.assertIn("OpenAI API connection failed", str(ctx.exception))

    async def test_end_to_end_retrieved_chunk_to_citation_traceability(self) -> None:
        """Integration-style test verifying full traceability chain: RetrievedChunk -> Answer -> Citation -> source Chunk."""
        mock_client = MagicMock()
        llm_payload = {
            "has_sufficient_evidence": True,
            "answer": "Promote the PostgreSQL replica node with 'pg_ctl promote' during primary outage.",
            "citations": [
                {
                    "chunk_id": self.retrieved_chunk_1.chunk_id,
                    "passage": self.retrieved_chunk_1.text,
                }
            ],
        }
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(llm_payload)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        service = GroundedGenerationService(client=mock_client)
        answer = await service.generate(
            query="How to handle PostgreSQL primary failure?",
            evidence=[self.retrieved_chunk_1],
        )

        # 1. Verify Answer structure
        self.assertEqual(answer.query, "How to handle PostgreSQL primary failure?")
        self.assertTrue(answer.has_sufficient_evidence)
        self.assertEqual(answer.evidence_status, EvidenceStatus.SUFFICIENT)

        # 2. Verify Citation links back to exact Chunk and Document
        self.assertEqual(len(answer.citations), 1)
        citation = answer.citations[0]
        self.assertEqual(citation.chunk_id, self.chunk_1.chunk_id)
        self.assertEqual(citation.document_id, self.chunk_1.document_id)
        self.assertEqual(citation.source_title, self.chunk_1.metadata["title"])
        self.assertEqual(citation.source_path, self.chunk_1.metadata["source_path"])
        self.assertEqual(citation.passage, self.chunk_1.text)
        self.assertEqual(citation.score, self.retrieved_chunk_1.score)


if __name__ == "__main__":
    unittest.main()

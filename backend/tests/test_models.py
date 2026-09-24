"""Unit tests for SourceWise RAG core data models."""

import unittest
from datetime import datetime

from pydantic import ValidationError

from app.models.chunk import Chunk
from app.models.citation import Citation
from app.models.document import Document
from app.models.generation import Answer, EvidenceStatus
from app.models.health import HealthResponse
from app.models.indexing import IndexingFailure, IndexingResult
from app.models.retrieval import RetrievalQuery, RetrievalResult, RetrievedChunk


class TestDocumentModel(unittest.TestCase):
    """Tests for the Document model."""

    def test_valid_document_creation_minimal(self) -> None:
        """Verify Document creation with required fields only."""
        doc = Document(
            document_id="doc_001",
            title="Postgres Runbook",
            content="Runbook contents for database recovery procedures.",
        )
        self.assertEqual(doc.document_id, "doc_001")
        self.assertEqual(doc.title, "Postgres Runbook")
        self.assertEqual(doc.content, "Runbook contents for database recovery procedures.")
        self.assertEqual(doc.source_type, "document")
        self.assertEqual(doc.access_level, "internal")
        self.assertEqual(doc.language, "en")
        self.assertIsNone(doc.product)
        self.assertIsNone(doc.version)
        self.assertIsNone(doc.department)
        self.assertIsNone(doc.owner)
        self.assertIsNone(doc.source_path)
        self.assertEqual(doc.metadata, {})

    def test_valid_document_creation_full_metadata(self) -> None:
        """Verify Document creation with full enterprise metadata."""
        now = datetime.now()
        doc = Document(
            document_id="doc_eng_042",
            title="Incident Response Guide",
            content="Steps to escalate production incidents.",
            source_type="markdown",
            source_path="docs/engineering/incident-response.md",
            product="SourceWise Core",
            version="2.1.0",
            department="DevOps",
            owner="oncall@company.com",
            last_updated=now,
            access_level="confidential",
            language="en",
            metadata={"priority": "P0", "team_slack": "#devops-oncall"},
        )
        self.assertEqual(doc.document_id, "doc_eng_042")
        self.assertEqual(doc.department, "DevOps")
        self.assertEqual(doc.access_level, "confidential")
        self.assertEqual(doc.metadata["priority"], "P0")

    def test_invalid_document_missing_required(self) -> None:
        """Verify validation errors when required fields are missing."""
        with self.assertRaises(ValidationError):
            Document(title="No ID", content="Content")  # type: ignore[call-arg]

        with self.assertRaises(ValidationError):
            Document(document_id="doc_1", content="Content")  # type: ignore[call-arg]

        with self.assertRaises(ValidationError):
            Document(document_id="doc_1", title="Title")  # type: ignore[call-arg]

    def test_invalid_document_empty_or_whitespace_fields(self) -> None:
        """Verify validation errors when fields are empty strings or whitespace."""
        with self.assertRaises(ValidationError):
            Document(document_id="   ", title="Title", content="Content")

        with self.assertRaises(ValidationError):
            Document(document_id="doc_1", title="", content="Content")

        with self.assertRaises(ValidationError):
            Document(document_id="doc_1", title="Title", content="   ")


class TestChunkModel(unittest.TestCase):
    """Tests for the Chunk model."""

    def test_valid_chunk_creation(self) -> None:
        """Verify Chunk creation and parent document provenance."""
        chunk = Chunk(
            chunk_id="doc_001#chunk_0",
            document_id="doc_001",
            text="Primary failover steps for PostgreSQL cluster.",
            chunk_index=0,
            token_count=120,
            metadata={"section": "Failover"},
        )
        self.assertEqual(chunk.chunk_id, "doc_001#chunk_0")
        self.assertEqual(chunk.document_id, "doc_001")
        self.assertEqual(chunk.chunk_index, 0)
        self.assertEqual(chunk.token_count, 120)
        self.assertEqual(chunk.metadata["section"], "Failover")

    def test_chunk_preserves_document_id(self) -> None:
        """Explicitly verify that a chunk maintains its parent document identity."""
        parent_doc_id = "doc_knowledge_base_99"
        chunk = Chunk(
            chunk_id=f"{parent_doc_id}#chunk_3",
            document_id=parent_doc_id,
            text="Passage text content.",
            chunk_index=3,
        )
        self.assertEqual(chunk.document_id, parent_doc_id)

    def test_invalid_chunk_negative_index_or_tokens(self) -> None:
        """Verify chunk validation for negative indices or token counts."""
        with self.assertRaises(ValidationError):
            Chunk(
                chunk_id="chunk_1",
                document_id="doc_1",
                text="Text",
                chunk_index=-1,
            )

        with self.assertRaises(ValidationError):
            Chunk(
                chunk_id="chunk_1",
                document_id="doc_1",
                text="Text",
                chunk_index=0,
                token_count=-5,
            )

    def test_invalid_chunk_blank_fields(self) -> None:
        """Verify validation failure for empty chunk IDs or empty text."""
        with self.assertRaises(ValidationError):
            Chunk(chunk_id="", document_id="doc_1", text="Text", chunk_index=0)

        with self.assertRaises(ValidationError):
            Chunk(chunk_id="c_1", document_id="  ", text="Text", chunk_index=0)

        with self.assertRaises(ValidationError):
            Chunk(chunk_id="c_1", document_id="doc_1", text="", chunk_index=0)


class TestRetrievedChunkModel(unittest.TestCase):
    """Tests for RetrievedChunk and Retrieval models."""

    def test_valid_retrieved_chunk(self) -> None:
        """Verify RetrievedChunk structure, ranking, scoring, and property helpers."""
        chunk = Chunk(
            chunk_id="doc_001#chunk_0",
            document_id="doc_001",
            text="Primary failover steps for PostgreSQL cluster.",
            chunk_index=0,
        )
        retrieved = RetrievedChunk(
            chunk=chunk,
            score=0.92,
            rank=1,
            retrieval_method="hybrid",
        )
        self.assertEqual(retrieved.chunk.chunk_id, "doc_001#chunk_0")
        self.assertEqual(retrieved.score, 0.92)
        self.assertEqual(retrieved.rank, 1)
        self.assertEqual(retrieved.retrieval_method, "hybrid")
        # Direct property helpers for provenance
        self.assertEqual(retrieved.document_id, "doc_001")
        self.assertEqual(retrieved.chunk_id, "doc_001#chunk_0")
        self.assertEqual(retrieved.text, chunk.text)

    def test_invalid_retrieved_chunk_rank(self) -> None:
        """Verify that rank must be >= 1."""
        chunk = Chunk(
            chunk_id="c1",
            document_id="d1",
            text="Text",
            chunk_index=0,
        )
        with self.assertRaises(ValidationError):
            RetrievedChunk(chunk=chunk, score=0.85, rank=0)

        with self.assertRaises(ValidationError):
            RetrievedChunk(chunk=chunk, score=0.85, rank=-1)

    def test_retrieval_query_and_result(self) -> None:
        """Verify RetrievalQuery and RetrievalResult containers."""
        query = RetrievalQuery(query="How to recover DB?", top_k=3, filters={"product": "SourceWise"})
        self.assertEqual(query.top_k, 3)
        self.assertEqual(query.filters["product"], "SourceWise")

        with self.assertRaises(ValidationError):
            RetrievalQuery(query="   ")

        result = RetrievalResult(query=query.query, retrieved_chunks=[], total_found=0)
        self.assertEqual(result.total_found, 0)


class TestCitationModel(unittest.TestCase):
    """Tests for the Citation model."""

    def test_valid_citation_creation(self) -> None:
        """Verify Citation with document and chunk traceability."""
        citation = Citation(
            citation_id="cite_1",
            document_id="doc_001",
            chunk_id="doc_001#chunk_0",
            source_title="PostgreSQL Runbook",
            passage="In case of primary failure, run pg_ctl promote.",
            source_path="docs/db/runbook.md",
            score=0.94,
        )
        self.assertEqual(citation.citation_id, "cite_1")
        self.assertEqual(citation.document_id, "doc_001")
        self.assertEqual(citation.chunk_id, "doc_001#chunk_0")
        self.assertEqual(citation.source_title, "PostgreSQL Runbook")
        self.assertEqual(citation.passage, "In case of primary failure, run pg_ctl promote.")

    def test_invalid_citation_missing_traceability(self) -> None:
        """Verify Citation fails if document_id, chunk_id, or passage are missing or blank."""
        with self.assertRaises(ValidationError):
            Citation(
                citation_id="cite_1",
                document_id="",
                chunk_id="chunk_1",
                source_title="Title",
                passage="Passage text",
            )

        with self.assertRaises(ValidationError):
            Citation(
                citation_id="cite_1",
                document_id="doc_1",
                chunk_id="   ",
                source_title="Title",
                passage="Passage text",
            )

        with self.assertRaises(ValidationError):
            Citation(
                citation_id="cite_1",
                document_id="doc_1",
                chunk_id="chunk_1",
                source_title="Title",
                passage="",
            )


class TestAnswerModel(unittest.TestCase):
    """Tests for the Answer model and end-to-end contract traceability."""

    def test_valid_answer_creation(self) -> None:
        """Verify Answer creation with complete citation and evidence payload."""
        chunk = Chunk(
            chunk_id="doc_001#chunk_0",
            document_id="doc_001",
            text="Primary failover steps for PostgreSQL cluster.",
            chunk_index=0,
        )
        retrieved = RetrievedChunk(chunk=chunk, score=0.92, rank=1)
        citation = Citation(
            citation_id="cite_1",
            document_id="doc_001",
            chunk_id="doc_001#chunk_0",
            source_title="Postgres Runbook",
            passage="Primary failover steps for PostgreSQL cluster.",
        )

        answer = Answer(
            query="How do I perform a database failover?",
            answer="To perform failover, promote the standby instance [1].",
            citations=[citation],
            evidence=[retrieved],
            confidence_score=0.95,
            evidence_status=EvidenceStatus.SUFFICIENT,
            has_sufficient_evidence=True,
            metadata={"latency_ms": 142},
        )

        self.assertEqual(answer.query, "How do I perform a database failover?")
        self.assertEqual(len(answer.citations), 1)
        self.assertEqual(len(answer.evidence), 1)
        self.assertEqual(answer.evidence_status, EvidenceStatus.SUFFICIENT)
        self.assertTrue(answer.has_sufficient_evidence)

    def test_answer_traceability_chain(self) -> None:
        """Verify the full chain: Answer -> Citation -> Chunk -> Document."""
        doc = Document(
            document_id="doc_auth_v2",
            title="Authentication Architecture",
            content="Tokens are signed with RS256 and expire in 1 hour.",
        )
        chunk = Chunk(
            chunk_id=f"{doc.document_id}#chunk_0",
            document_id=doc.document_id,
            text="Tokens are signed with RS256 and expire in 1 hour.",
            chunk_index=0,
        )
        retrieved = RetrievedChunk(chunk=chunk, score=0.98, rank=1)
        citation = Citation(
            citation_id="cite_auth_1",
            document_id=doc.document_id,
            chunk_id=chunk.chunk_id,
            source_title=doc.title,
            passage=chunk.text,
        )
        answer = Answer(
            query="What is the token expiration period?",
            answer="Authentication tokens expire in 1 hour [cite_auth_1].",
            citations=[citation],
            evidence=[retrieved],
        )

        # Verify end-to-end chain
        self.assertEqual(answer.citations[0].chunk_id, chunk.chunk_id)
        self.assertEqual(answer.citations[0].document_id, doc.document_id)
        self.assertEqual(answer.evidence[0].document_id, doc.document_id)

    def test_invalid_answer_blank_query(self) -> None:
        """Verify Answer rejects blank questions."""
        with self.assertRaises(ValidationError):
            Answer(query="   ", answer="Some answer")


class TestIndexingModels(unittest.TestCase):
    """Tests for IndexingResult and IndexingFailure models."""

    def test_indexing_result_defaults(self) -> None:
        """Verify default initialization of IndexingResult."""
        result = IndexingResult()
        self.assertEqual(result.documents_processed, 0)
        self.assertEqual(result.chunks_created, 0)
        self.assertEqual(result.chunks_indexed, 0)
        self.assertEqual(result.point_ids, [])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.failures, [])
        self.assertTrue(result.is_success)
        self.assertFalse(result.has_failures)

    def test_indexing_result_populated(self) -> None:
        """Verify IndexingResult with counts, point IDs, and failures."""
        failure = IndexingFailure(
            document_id="doc_bad",
            stage="chunking",
            error="Failed to chunk document: parsing error",
        )
        result = IndexingResult(
            documents_processed=2,
            chunks_created=5,
            chunks_indexed=5,
            point_ids=["p1", "p2", "p3", "p4", "p5"],
            errors=["Warning: doc_bad chunking issue"],
            failures=[failure],
        )
        self.assertEqual(result.documents_processed, 2)
        self.assertEqual(result.chunks_created, 5)
        self.assertEqual(result.chunks_indexed, 5)
        self.assertEqual(len(result.point_ids), 5)
        self.assertFalse(result.is_success)
        self.assertTrue(result.has_failures)
        self.assertEqual(result.failures[0].document_id, "doc_bad")
        self.assertEqual(result.failures[0].stage, "chunking")

        # Iterable and indexing convenience
        self.assertEqual(list(result), ["p1", "p2", "p3", "p4", "p5"])
        self.assertEqual(result[0], "p1")
        self.assertEqual(len(result), 5)

        # List equality check
        self.assertEqual(result, ["p1", "p2", "p3", "p4", "p5"])


if __name__ == "__main__":
    unittest.main()

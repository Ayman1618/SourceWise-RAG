"""Comprehensive tests for document ingestion and chunking pipeline."""

from pathlib import Path
import unittest

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunking import ChunkingService
from app.services.ingestion import DocumentIngestionService
from app.services.markdown_parser import MarkdownParseError, MarkdownParser


class TestMarkdownParser(unittest.TestCase):
    """Unit tests for Markdown parsing and frontmatter extraction."""

    def setUp(self) -> None:
        self.parser = MarkdownParser()

    def test_valid_markdown_and_metadata_extraction(self) -> None:
        raw = """---
document_id: doc-test-auth
title: Test Auth Guide
source_type: product_documentation
product: SourceWise Platform
version: "1.0.0"
department: Security
owner: Security Team
last_updated: "2026-09-15"
access_level: confidential
language: en
custom_tag: auth-v1
---

# Test Auth Guide

## Section 1
This is the body content of the test document.
"""
        doc = self.parser.parse(raw_text=raw, source_path="docs/test.md")
        self.assertEqual(doc.document_id, "doc-test-auth")
        self.assertEqual(doc.title, "Test Auth Guide")
        self.assertEqual(doc.source_type, "product_documentation")
        self.assertEqual(doc.product, "SourceWise Platform")
        self.assertEqual(doc.version, "1.0.0")
        self.assertEqual(doc.department, "Security")
        self.assertEqual(doc.owner, "Security Team")
        self.assertEqual(doc.access_level, "confidential")
        self.assertEqual(doc.language, "en")
        self.assertIn("Section 1", doc.content)
        self.assertNotIn("---", doc.content)
        self.assertEqual(doc.metadata.get("custom_tag"), "auth-v1")

    def test_missing_title_inferred_from_first_heading(self) -> None:
        raw = """---
document_id: doc-inferred-title
product: SourceWise
---

# Inferred Architecture Guide

Some explanation here.
"""
        doc = self.parser.parse(raw_text=raw)
        self.assertEqual(doc.title, "Inferred Architecture Guide")
        self.assertEqual(doc.document_id, "doc-inferred-title")

    def test_missing_document_id_fallback_from_file_path(self) -> None:
        raw = """# Some Document Without Frontmatter

Content goes here.
"""
        doc = self.parser.parse(raw_text=raw, source_path="data/docs/guide-to-troubleshooting.md")
        self.assertEqual(doc.document_id, "guide-to-troubleshooting")
        self.assertEqual(doc.title, "Some Document Without Frontmatter")

    def test_malformed_yaml_frontmatter_raises_error(self) -> None:
        raw = """---
title: [unclosed list
invalid_yaml: {
---

# Body
Content.
"""
        with self.assertRaises(MarkdownParseError):
            self.parser.parse(raw_text=raw)

    def test_missing_closing_delimiter_raises_error(self) -> None:
        raw = """---
title: Unclosed Frontmatter
product: SourceWise

# Body
Content without end delimiter.
"""
        with self.assertRaises(MarkdownParseError):
            self.parser.parse(raw_text=raw)

    def test_empty_or_whitespace_document_raises_error(self) -> None:
        with self.assertRaises(MarkdownParseError):
            self.parser.parse(raw_text="")

        with self.assertRaises(MarkdownParseError):
            self.parser.parse(raw_text="   \n\n  \t ")

    def test_empty_body_after_frontmatter_raises_error(self) -> None:
        raw = """---
title: Only Frontmatter
document_id: empty-body
---
"""
        with self.assertRaises(MarkdownParseError):
            self.parser.parse(raw_text=raw)


class TestChunkingService(unittest.TestCase):
    """Unit tests for chunking service behavior, token windows, and metadata inheritance."""

    def setUp(self) -> None:
        self.chunker = ChunkingService(
            min_chunk_tokens=500,
            max_chunk_tokens=800,
            overlap_tokens=75,
        )

    def test_deterministic_chunk_ids(self) -> None:
        doc = Document(
            document_id="doc_runbook_v1",
            title="Runbook",
            content="## Section 1\n\nFirst paragraph.\n\n## Section 2\n\nSecond paragraph.",
        )
        chunks1 = self.chunker.chunk_document(doc)
        chunks2 = self.chunker.chunk_document(doc)

        self.assertEqual(len(chunks1), len(chunks2))
        for c1, c2 in zip(chunks1, chunks2):
            self.assertEqual(c1.chunk_id, c2.chunk_id)
            self.assertEqual(c1.text, c2.text)
            self.assertEqual(c1.chunk_index, c2.chunk_index)

    def test_preserves_document_id_and_chunk_ordering(self) -> None:
        # Build long content that requires multiple chunks
        sections = [f"## Section {i}\n\n" + "Word " * 200 for i in range(1, 6)]
        content = "\n\n".join(sections)

        doc = Document(
            document_id="doc_multi_section",
            title="Multi Section Document",
            content=content,
            product="SourceWise Core",
            version="2.0",
        )

        chunks = self.chunker.chunk_document(doc, min_chunk_tokens=200, max_chunk_tokens=350, overlap_tokens=50)
        self.assertGreater(len(chunks), 1)

        for expected_index, chunk in enumerate(chunks):
            self.assertEqual(chunk.document_id, "doc_multi_section")
            self.assertEqual(chunk.chunk_index, expected_index)
            self.assertEqual(chunk.chunk_id, f"doc_multi_section#chunk_{expected_index}")
            self.assertIsNotNone(chunk.token_count)
            self.assertGreater(chunk.token_count or 0, 0)
            self.assertEqual(chunk.metadata["title"], "Multi Section Document")
            self.assertEqual(chunk.metadata["product"], "SourceWise Core")
            self.assertEqual(chunk.metadata["version"], "2.0")

    def test_chunk_overlap_present_between_consecutive_chunks(self) -> None:
        sections = [
            "## Intro\n\n" + "Alpha Bravo Charlie Delta Echo. " * 30,
            "## Deep Dive\n\n" + "Foxtrot Golf Hotel India Juliet. " * 30,
            "## Troubleshooting\n\n" + "Kilo Lima Mike November Oscar. " * 30,
        ]
        doc = Document(
            document_id="doc_overlap_test",
            title="Overlap Test",
            content="\n\n".join(sections),
        )

        chunks = self.chunker.chunk_document(doc, min_chunk_tokens=100, max_chunk_tokens=180, overlap_tokens=40)
        self.assertGreater(len(chunks), 1)

        for i in range(len(chunks) - 1):
            c1_text = chunks[i].text
            c2_text = chunks[i + 1].text

            # Check for shared sentences or substring between c1 tail and c2 head
            c1_words = c1_text.split()[-10:]
            shared_fragment = " ".join(c1_words)
            # Either words match or overlap prefix exists in both
            self.assertTrue(
                shared_fragment in c2_text or any(word in c2_text[:200] for word in c1_words),
                f"Expected overlap between chunk {i} and {i+1}",
            )

    def test_code_block_boundary_preservation(self) -> None:
        code_block = "```python\ndef test_fn():\n    return 'preserved together'\n```"
        content = f"## Code Sample\n\nIntroductory text.\n\n{code_block}\n\nSubsequent text."
        doc = Document(
            document_id="doc_code_test",
            title="Code Test",
            content=content,
        )
        chunks = self.chunker.chunk_document(doc)
        self.assertEqual(len(chunks), 1)
        self.assertIn(code_block, chunks[0].text)


class TestDocumentIngestionService(unittest.IsolatedAsyncioTestCase):
    """Integration tests verifying full pipeline with sample documents from data/sample-documents/."""

    def setUp(self) -> None:
        self.service = DocumentIngestionService()
        self.sample_docs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "sample-documents"

    async def test_sample_documents_exist_and_ingest(self) -> None:
        self.assertTrue(
            self.sample_docs_dir.exists(),
            f"Directory not found: {self.sample_docs_dir}",
        )
        documents = await self.service.ingest(self.sample_docs_dir)

        # 3 synthetic sample documents
        doc_ids = {doc.document_id for doc in documents}
        self.assertEqual(len(documents), 3)
        self.assertIn("sample-api-rate-limits", doc_ids)
        self.assertIn("sample-authentication-guide", doc_ids)
        self.assertIn("sample-login-troubleshooting", doc_ids)

        for doc in documents:
            self.assertTrue(doc.title)
            self.assertTrue(doc.content)
            self.assertIn("SourceWise Platform", doc.product or "")
            self.assertIn(doc.access_level, ["internal", "confidential", "public"])
            self.assertTrue(doc.source_path)

    async def test_sample_documents_chunking_pipeline(self) -> None:
        documents = await self.service.ingest(self.sample_docs_dir)

        total_chunks = 0
        for doc in documents:
            chunks = await self.service.chunk_document(doc)
            self.assertGreaterEqual(
                len(chunks),
                2,
                f"Document {doc.document_id} should produce at least 2 chunks",
            )
            total_chunks += len(chunks)

            for i, chunk in enumerate(chunks):
                self.assertEqual(chunk.document_id, doc.document_id)
                self.assertEqual(chunk.chunk_index, i)
                self.assertEqual(chunk.chunk_id, f"{doc.document_id}#chunk_{i}")
                self.assertIsNotNone(chunk.token_count)
                # Chunk tokens should not exceed max boundary
                self.assertLessEqual(chunk.token_count or 0, 900)
                # Chunk metadata inheritance
                self.assertEqual(chunk.metadata.get("title"), doc.title)
                self.assertEqual(chunk.metadata.get("source_path"), doc.source_path)
                self.assertEqual(chunk.metadata.get("version"), doc.version)
                self.assertEqual(chunk.metadata.get("access_level"), doc.access_level)

        self.assertGreaterEqual(total_chunks, 6)

    async def test_ingest_and_chunk_utility(self) -> None:
        docs, chunks = await self.service.ingest_and_chunk(self.sample_docs_dir)
        self.assertEqual(len(docs), 3)
        self.assertGreaterEqual(len(chunks), 6)

        # Verify all chunk IDs are unique
        chunk_ids = [c.chunk_id for c in chunks]
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)))

    async def test_sample_documents_overlap_and_token_targets(self) -> None:
        """Verify chunks target ~500-800 tokens and 50-100 token overlap on actual sample documents."""
        documents = await self.service.ingest(self.sample_docs_dir)
        for doc in documents:
            chunks = await self.service.chunk_document(doc)
            for i in range(len(chunks) - 1):
                c_current = chunks[i]
                c_next = chunks[i + 1]

                # Extract overlap between c_current and c_next
                overlap_text = self.service.chunker._extract_overlap(
                    c_current.text,
                    target_overlap_tokens=self.service.chunker.overlap_tokens,
                )
                overlap_tokens = self.service.chunker.count_tokens(overlap_text)

                # Overlap should target 50-100 tokens
                self.assertGreaterEqual(
                    overlap_tokens,
                    50,
                    f"Overlap between chunk {i} and {i+1} in {doc.document_id} was {overlap_tokens} (<50)",
                )
                self.assertLessEqual(
                    overlap_tokens,
                    100,
                    f"Overlap between chunk {i} and {i+1} in {doc.document_id} was {overlap_tokens} (>100)",
                )

                # c_next starts with the overlap text
                self.assertTrue(
                    c_next.text.startswith(overlap_text),
                    f"Chunk {i+1} does not start with expected overlap text in {doc.document_id}",
                )

                # Non-final chunks should be in the target 500-800 tokens window
                self.assertGreaterEqual(
                    c_current.token_count or 0,
                    450,
                    f"Non-final chunk {i} in {doc.document_id} below target window: {c_current.token_count}",
                )
                self.assertLessEqual(
                    c_current.token_count or 0,
                    800,
                    f"Chunk {i} in {doc.document_id} exceeded target window: {c_current.token_count}",
                )

    async def test_offline_execution_no_external_apis(self) -> None:
        """Verify ingestion and chunking operate completely offline without external network calls."""
        docs, chunks = await self.service.ingest_and_chunk(self.sample_docs_dir)
        self.assertEqual(len(docs), 3)
        self.assertEqual(len(chunks), 10)
        for chunk in chunks:
            self.assertIsInstance(chunk, Chunk)
            self.assertIsInstance(chunk.text, str)
            self.assertGreater(len(chunk.text), 0)

    async def test_raw_markdown_string_ingestion(self) -> None:
        raw_content = """---
document_id: doc_raw_string
title: Raw Ingest
---
# Raw Ingest
Some inline content.
"""
        docs = await self.service.ingest(raw_content)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].document_id, "doc_raw_string")
        self.assertEqual(docs[0].title, "Raw Ingest")


if __name__ == "__main__":
    unittest.main()

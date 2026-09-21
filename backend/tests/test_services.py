"""Unit tests for pipeline service interfaces."""

import unittest
from pathlib import Path
from typing import Any

from app.models.chunk import Chunk
from app.models.citation import Citation
from app.models.document import Document
from app.models.generation import Answer
from app.models.retrieval import RetrievalQuery, RetrievedChunk
from app.services.embedding import BaseEmbeddingService
from app.services.generation import BaseGenerationService
from app.services.ingestion import BaseIngestionService
from app.services.retrieval import BaseRetrievalService
from app.services.vector_store import BaseVectorStoreService


class TestServiceInterfaces(unittest.TestCase):
    """Tests verifying abstract service contracts and subclass implementations."""

    def test_abstract_services_cannot_be_instantiated_directly(self) -> None:
        """Verify abstract base classes enforce implementation of abstract methods."""
        with self.assertRaises(TypeError):
            BaseIngestionService()  # type: ignore[abstract]

        with self.assertRaises(TypeError):
            BaseRetrievalService()  # type: ignore[abstract]

        with self.assertRaises(TypeError):
            BaseGenerationService()  # type: ignore[abstract]

        with self.assertRaises(TypeError):
            BaseEmbeddingService()  # type: ignore[abstract]

        with self.assertRaises(TypeError):
            BaseVectorStoreService()  # type: ignore[abstract]


    def test_concrete_mock_implementations(self) -> None:
        """Verify services can be cleanly subclassed according to contracts."""

        class MockIngestionService(BaseIngestionService):
            async def ingest(
                self, source: str | Path | dict[str, Any], **kwargs: Any
            ) -> list[Document]:
                return [
                    Document(
                        document_id="mock_doc",
                        title="Mock Document",
                        content="Mock Content",
                    )
                ]

            async def chunk_document(
                self, document: Document, **kwargs: Any
            ) -> list[Chunk]:
                return [
                    Chunk(
                        chunk_id=f"{document.document_id}#chunk_0",
                        document_id=document.document_id,
                        text=document.content,
                        chunk_index=0,
                    )
                ]

        class MockRetrievalService(BaseRetrievalService):
            async def retrieve(
                self,
                query: str | RetrievalQuery,
                top_k: int = 5,
                filters: dict[str, Any] | None = None,
                **kwargs: Any,
            ) -> list[RetrievedChunk]:
                chunk = Chunk(
                    chunk_id="doc_1#chunk_0",
                    document_id="doc_1",
                    text="Retrieved passage",
                    chunk_index=0,
                )
                return [RetrievedChunk(chunk=chunk, score=0.95, rank=1)]

        class MockGenerationService(BaseGenerationService):
            async def generate(
                self,
                query: str,
                evidence: list[RetrievedChunk],
                **kwargs: Any,
            ) -> Answer:
                citations = [
                    Citation(
                        citation_id=f"cite_{item.rank}",
                        document_id=item.document_id,
                        chunk_id=item.chunk_id,
                        source_title="Mock Doc",
                        passage=item.text,
                    )
                    for item in evidence
                ]
                return Answer(
                    query=query,
                    answer="Generated response based on evidence.",
                    citations=citations,
                    evidence=evidence,
                )

        # Instantiation check
        ingestion = MockIngestionService()
        retrieval = MockRetrievalService()
        generation = MockGenerationService()

        self.assertIsInstance(ingestion, BaseIngestionService)
        self.assertIsInstance(retrieval, BaseRetrievalService)
        self.assertIsInstance(generation, BaseGenerationService)


if __name__ == "__main__":
    unittest.main()

"""Pipeline interface and implementation for document ingestion and chunking services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunking import ChunkingService
from app.services.markdown_parser import MarkdownParser


class BaseIngestionService(ABC):
    """Abstract contract for document ingestion, parsing, and chunking."""

    @abstractmethod
    async def ingest(
        self,
        source: str | Path | dict[str, Any],
        **kwargs: Any,
    ) -> list[Document]:
        """Normalize raw document sources into standard Document instances.

        Args:
            source: Source path, file URI, or dictionary containing raw document payload.
            **kwargs: Additional ingestion configuration.

        Returns:
            list[Document]: One or more normalized Document instances.
        """
        raise NotImplementedError

    @abstractmethod
    async def chunk_document(
        self,
        document: Document,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split a normalized Document into discrete, traceable Chunk instances.

        Args:
            document: Normalized parent Document to segment.
            **kwargs: Additional chunking configuration (e.g. chunk_size, chunk_overlap).

        Returns:
            list[Chunk]: List of extracted Chunk objects preserving document_id.
        """
        raise NotImplementedError


class DocumentIngestionService(BaseIngestionService):
    """Production implementation of document ingestion and chunking pipeline."""

    def __init__(
        self,
        parser: MarkdownParser | None = None,
        chunker: ChunkingService | None = None,
    ) -> None:
        """Initialize the document ingestion service.

        Args:
            parser: Markdown parser instance (defaults to MarkdownParser()).
            chunker: Chunking service instance (defaults to ChunkingService()).
        """
        self.parser = parser or MarkdownParser()
        self.chunker = chunker or ChunkingService()

    async def ingest(
        self,
        source: str | Path | dict[str, Any],
        encoding: str = "utf-8",
        include_readme: bool = False,
        **kwargs: Any,
    ) -> list[Document]:
        """Normalize raw document sources into standard Document instances.

        Supports:
        - Path or directory string (e.g., 'data/sample-documents/')
        - Single file Path or file path string
        - Raw Markdown text string
        - Raw dictionary representing Document fields

        Args:
            source: Path to file/directory, raw markdown string, or dictionary.
            encoding: Text encoding for file reads (default: utf-8).
            include_readme: Whether to include README.md when ingesting a directory (default: False).
            **kwargs: Additional arguments forwarded to parser or document factory.

        Returns:
            list[Document]: List of normalized Document objects.
        """
        if isinstance(source, dict):
            return [Document(**source)]

        # Check if source is a filesystem path
        path_candidate: Path | None = None
        if isinstance(source, Path):
            path_candidate = source
        elif isinstance(source, str):
            p = Path(source)
            if p.exists() or (len(source) < 500 and ("/" in source or "\\" in source or source.endswith(".md"))):
                path_candidate = p

        if path_candidate and path_candidate.exists():
            if path_candidate.is_dir():
                documents: list[Document] = []
                for md_file in sorted(path_candidate.glob("*.md")):
                    if not include_readme and md_file.name.lower() == "readme.md":
                        continue
                    doc = self.parser.parse_file(md_file, encoding=encoding, **kwargs)
                    documents.append(doc)
                return documents
            elif path_candidate.is_file():
                return [self.parser.parse_file(path_candidate, encoding=encoding, **kwargs)]

        # Treat source as raw markdown text content
        if isinstance(source, str):
            source_path = kwargs.pop("source_path", None)
            return [self.parser.parse(raw_text=source, source_path=source_path, **kwargs)]

        raise ValueError(f"Unsupported source type: {type(source)}")

    async def chunk_document(
        self,
        document: Document,
        **kwargs: Any,
    ) -> list[Chunk]:
        """Split a normalized Document into discrete, traceable Chunk instances.

        Preserves:
        - document_id
        - chunk_id (deterministic format: {document_id}#chunk_{chunk_index})
        - chunk_index (sequential 0-indexed position)
        - source metadata inherited from document
        - text content

        Args:
            document: Canonical Document object to segment.
            **kwargs: Chunking parameters (e.g. min_chunk_tokens, max_chunk_tokens, overlap_tokens).

        Returns:
            list[Chunk]: Traceable chunks adhering to token and boundary requirements.
        """
        return self.chunker.chunk_document(document, **kwargs)

    async def ingest_and_chunk(
        self,
        source: str | Path | dict[str, Any],
        **kwargs: Any,
    ) -> tuple[list[Document], list[Chunk]]:
        """Ingest document sources and immediately segment them into traceable Chunks.

        Args:
            source: File path, directory, raw text, or dictionary.
            **kwargs: Ingestion and chunking options.

        Returns:
            tuple[list[Document], list[Chunk]]: Ingested documents and resulting chunks.
        """
        documents = await self.ingest(source, **kwargs)
        all_chunks: list[Chunk] = []
        for doc in documents:
            chunks = await self.chunk_document(doc, **kwargs)
            all_chunks.extend(chunks)
        return documents, all_chunks

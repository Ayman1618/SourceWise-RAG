"""Pipeline interface for document ingestion and chunking services."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.models.chunk import Chunk
from app.models.document import Document


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

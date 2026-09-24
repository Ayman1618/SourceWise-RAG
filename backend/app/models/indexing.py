"""Data models for document and chunk indexing pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IndexingFailure(BaseModel):
    """Details of an error or failure encountered during indexing."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    document_id: str | None = Field(
        default=None,
        description="ID of the document that encountered the error, if applicable",
    )
    chunk_id: str | None = Field(
        default=None,
        description="ID of the chunk that encountered the error, if applicable",
    )
    stage: str = Field(
        ...,
        description="Indexing pipeline stage where failure occurred (e.g. 'chunking', 'embedding', 'vector_store')",
    )
    error: str = Field(
        ...,
        description="Error message describing the failure",
    )


class IndexingResult(BaseModel):
    """Structured result returned by the document indexing pipeline."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    documents_processed: int = Field(
        default=0,
        ge=0,
        description="Number of documents successfully processed",
    )
    chunks_created: int = Field(
        default=0,
        ge=0,
        description="Total number of chunks generated from processed documents",
    )
    chunks_indexed: int = Field(
        default=0,
        ge=0,
        description="Number of chunks successfully embedded and persisted to vector store",
    )
    point_ids: list[str] = Field(
        default_factory=list,
        description="List of deterministic vector point IDs stored in the vector database",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of human-readable error descriptions encountered during indexing",
    )
    failures: list[IndexingFailure] = Field(
        default_factory=list,
        description="Structured failure objects detailing stage and context of failures",
    )

    @property
    def is_success(self) -> bool:
        """True if indexing completed without any errors or failures."""
        return len(self.errors) == 0 and len(self.failures) == 0

    @property
    def has_failures(self) -> bool:
        """True if any failures were encountered during indexing."""
        return not self.is_success

    def __iter__(self):
        """Allow iterating directly over point IDs for convenience and backward compatibility."""
        return iter(self.point_ids)

    def __getitem__(self, index: int) -> str:
        """Allow indexing into point IDs for convenience and backward compatibility."""
        return self.point_ids[index]

    def __len__(self) -> int:
        """Length is the count of indexed points."""
        return len(self.point_ids)

    def __eq__(self, other: Any) -> bool:
        """Support equality check against a list of point IDs or another IndexingResult."""
        if isinstance(other, list):
            return self.point_ids == other
        return super().__eq__(other)

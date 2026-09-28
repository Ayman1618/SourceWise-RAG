"""Retrieved evidence and retrieval query models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.chunk import Chunk


class RetrievedChunk(BaseModel):
    """Represents an evidence passage retrieved for a query with scoring and ranking.

    Wraps the underlying Chunk to maintain full provenance and document traceability.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    chunk: Chunk = Field(
        ...,
        description="The retrieved Chunk containing text and parent document metadata",
    )
    score: float = Field(
        ...,
        description="Similarity or relevance score computed by the retrieval or reranking engine",
        examples=[0.89],
    )
    rank: int = Field(
        ...,
        ge=1,
        description="1-indexed rank position of the retrieved chunk in the result set",
        examples=[1],
    )
    retrieval_method: str | None = Field(
        default=None,
        description="Method used to retrieve this chunk (e.g., dense, sparse, hybrid, reranked)",
        examples=["hybrid"],
    )

    @property
    def document_id(self) -> str:
        """Convenience property to access parent document ID."""
        return self.chunk.document_id

    @property
    def chunk_id(self) -> str:
        """Convenience property to access chunk ID."""
        return self.chunk.chunk_id

    @property
    def text(self) -> str:
        """Convenience property to access chunk text."""
        return self.chunk.text

    @property
    def metadata(self) -> dict[str, Any]:
        """Convenience property to access chunk metadata dictionary."""
        return self.chunk.metadata

    @property
    def title(self) -> str | None:
        """Convenience property to access document title from chunk metadata."""
        return self.chunk.metadata.get("title")

    @property
    def source_type(self) -> str | None:
        """Convenience property to access document source_type from chunk metadata."""
        return self.chunk.metadata.get("source_type")

    @property
    def product(self) -> str | None:
        """Convenience property to access product from chunk metadata."""
        return self.chunk.metadata.get("product")

    @property
    def version(self) -> str | None:
        """Convenience property to access version from chunk metadata."""
        return self.chunk.metadata.get("version")

    @property
    def department(self) -> str | None:
        """Convenience property to access department from chunk metadata."""
        return self.chunk.metadata.get("department")

    @property
    def owner(self) -> str | None:
        """Convenience property to access owner from chunk metadata."""
        return self.chunk.metadata.get("owner")

    @property
    def last_updated(self) -> Any:
        """Convenience property to access last_updated from chunk metadata."""
        return self.chunk.metadata.get("last_updated")

    @property
    def access_level(self) -> str | None:
        """Convenience property to access access_level from chunk metadata."""
        return self.chunk.metadata.get("access_level")

    @property
    def language(self) -> str | None:
        """Convenience property to access language from chunk metadata."""
        return self.chunk.metadata.get("language")

    @property
    def source_path(self) -> str | None:
        """Convenience property to access source_path from chunk metadata."""
        return self.chunk.metadata.get("source_path")


class RetrievalQuery(BaseModel):
    """Represents retrieval request parameters."""

    query: str = Field(
        ...,
        min_length=1,
        description="Search query string",
        examples=["How do I recover the PostgreSQL database?"],
    )
    top_k: int = Field(
        default=5,
        gt=0,
        description="Maximum number of chunks to retrieve",
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata filters for targeted retrieval",
    )

    @field_validator("query", mode="before")
    @classmethod
    def validate_query_not_blank(cls, value: Any) -> Any:
        """Ensure query is not empty or whitespace only."""
        if isinstance(value, str) and not value.strip():
            raise ValueError("query cannot be empty or whitespace only")
        return value


class RetrievalResult(BaseModel):
    """Container for retrieval query results."""

    query: str = Field(..., description="Original search query")
    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Ordered list of retrieved chunks meeting the search criteria",
    )
    total_found: int = Field(
        default=0,
        ge=0,
        description="Total count of candidate chunks identified",
    )

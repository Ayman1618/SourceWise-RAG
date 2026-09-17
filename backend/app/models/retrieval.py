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

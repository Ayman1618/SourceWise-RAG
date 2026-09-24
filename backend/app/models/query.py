"""Query request schemas for API validation and orchestration."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryRequest(BaseModel):
    """Request payload for RAG query execution."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User question to query against internal knowledge base",
        examples=["How do I troubleshoot repeated login failures?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of evidence chunks to retrieve",
        examples=[5],
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata filtering criteria for targeted retrieval",
        examples=[{"department": "engineering"}],
    )

    @field_validator("query", mode="before")
    @classmethod
    def validate_query_not_blank(cls, value: Any) -> Any:
        """Ensure query is trimmed and not empty or whitespace only."""
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                raise ValueError("Query cannot be empty or whitespace only")
            return trimmed
        return value

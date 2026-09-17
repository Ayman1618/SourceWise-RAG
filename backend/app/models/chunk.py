"""Chunk model representing a discrete segment of a document."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Chunk(BaseModel):
    """Represents a discrete text segment extracted from a parent Document.

    Preserves parent document identity to ensure complete citation traceability.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    chunk_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the chunk",
        examples=["doc_runbook_v1#chunk_0"],
    )
    document_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the parent document from which this chunk was extracted",
        examples=["doc_runbook_v1"],
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Text content of the extracted chunk",
    )
    chunk_index: int = Field(
        ...,
        ge=0,
        description="0-indexed position of this chunk within the parent document sequence",
        examples=[0],
    )
    token_count: int | None = Field(
        default=None,
        ge=0,
        description="Optional estimated or measured token count for this chunk",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk-level or inherited metadata",
    )

    @field_validator("chunk_id", "document_id", "text", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, value: Any, info: Any) -> Any:
        """Ensure string identifiers and text are not blank."""
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")
        return value

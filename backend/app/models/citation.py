"""Citation model for grounded answer attribution."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Citation(BaseModel):
    """Represents an exact source reference supporting a factual statement in an answer.

    Guarantees strict traceability from the generated answer back to the parent Document and Chunk.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    citation_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the citation reference",
        examples=["cite_1"],
    )
    document_id: str = Field(
        ...,
        min_length=1,
        description="Traceable identifier of the parent source document",
        examples=["doc_runbook_v1"],
    )
    chunk_id: str = Field(
        ...,
        min_length=1,
        description="Traceable identifier of the specific source chunk",
        examples=["doc_runbook_v1#chunk_0"],
    )
    source_title: str = Field(
        ...,
        min_length=1,
        description="Title of the cited source document for display to the user",
        examples=["Database Recovery Runbook"],
    )
    passage: str = Field(
        ...,
        min_length=1,
        description="Exact excerpt or text passage from the source chunk supporting the answer",
        examples=["In case of primary failure, promote the hot standby with pg_ctl promote."],
    )
    source_path: str | None = Field(
        default=None,
        description="Optional link or path to the source document",
        examples=["docs/engineering/runbook.md"],
    )
    score: float | None = Field(
        default=None,
        description="Optional relevance or attribution score for this citation",
    )

    @field_validator(
        "citation_id", "document_id", "chunk_id", "source_title", "passage", mode="before"
    )
    @classmethod
    def validate_non_empty_fields(cls, value: Any, info: Any) -> Any:
        """Ensure all required traceability fields are not blank."""
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")
        return value

"""Normalized source document data model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    """Represents a normalized source document within the SourceWise knowledge base."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    document_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the document",
        examples=["doc_engineering_runbook_v1"],
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Title or heading of the source document",
        examples=["Database Recovery Runbook"],
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Full text or raw extracted body of the document",
    )
    source_type: str = Field(
        default="document",
        description="Type or format of the source (e.g., markdown, pdf, confluence, ticket)",
        examples=["markdown"],
    )
    source_path: str | None = Field(
        default=None,
        description="URI, file path, or URL pointing to the original document source",
        examples=["docs/engineering/runbook.md"],
    )
    product: str | None = Field(
        default=None,
        description="Product or system associated with the document",
        examples=["SourceWise Core"],
    )
    version: str | None = Field(
        default=None,
        description="Document or software version",
        examples=["1.2.0"],
    )
    department: str | None = Field(
        default=None,
        description="Organizational department or team owning the document",
        examples=["Engineering"],
    )
    owner: str | None = Field(
        default=None,
        description="Document author, owner, or maintainer",
        examples=["infrastructure-team@company.com"],
    )
    last_updated: datetime | str | None = Field(
        default=None,
        description="Timestamp or ISO date string when the source was last modified",
    )
    access_level: str | None = Field(
        default="internal",
        description="Access or clearance level required (e.g., public, internal, confidential)",
        examples=["internal"],
    )
    language: str = Field(
        default="en",
        description="ISO language code of the document content",
        examples=["en"],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible custom metadata attributes",
    )

    @field_validator("document_id", "title", "content", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, value: Any, info: Any) -> Any:
        """Ensure critical string fields are not purely whitespace."""
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace only")
        return value

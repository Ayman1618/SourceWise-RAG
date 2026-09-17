"""Grounded answer and generation response models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.citation import Citation
from app.models.retrieval import RetrievedChunk


class EvidenceStatus(str, Enum):
    """Status indicating the grounding confidence and evidence availability."""

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    REFUSED = "refused"
    UNVERIFIED = "unverified"


class Answer(BaseModel):
    """Represents a grounded answer generated from retrieved evidence.

    Structured to deliver the complete response contract:
    Question → Answer → Citations/Evidence.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    query: str = Field(
        ...,
        min_length=1,
        description="User query or prompt that was answered",
        examples=["How do I recover the PostgreSQL database?"],
    )
    answer: str = Field(
        ...,
        description="Generated response grounded in retrieved evidence or refusal notice",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="List of verifiable source citations backing statements in the answer",
    )
    evidence: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Retrieved evidence chunks evaluated during answer generation",
    )
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional calibrated confidence score (0.0 to 1.0)",
    )
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.SUFFICIENT,
        description="Evidence sufficiency classification (sufficient, insufficient, refused)",
    )
    has_sufficient_evidence: bool = Field(
        default=True,
        description="Boolean flag indicating whether sufficient grounded evidence was found",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata (e.g. latency, token usage, model id)",
    )

    @field_validator("query", mode="before")
    @classmethod
    def validate_query_not_blank(cls, value: Any) -> Any:
        """Ensure query is not empty or whitespace only."""
        if isinstance(value, str) and not value.strip():
            raise ValueError("query cannot be empty or whitespace only")
        return value

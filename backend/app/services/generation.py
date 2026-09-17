"""Pipeline interface for grounded answer generation and citation synthesis."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.generation import Answer
from app.models.retrieval import RetrievedChunk


class BaseGenerationService(ABC):
    """Abstract contract for evidence-grounded answer generation."""

    @abstractmethod
    async def generate(
        self,
        query: str,
        evidence: list[RetrievedChunk],
        **kwargs: Any,
    ) -> Answer:
        """Generate a factual answer grounded strictly in retrieved evidence.

        Args:
            query: The user question to be answered.
            evidence: List of retrieved evidence chunks to ground the generation.
            **kwargs: Additional generation options (e.g. temperature, max tokens).

        Returns:
            Answer: Grounded response containing the answer text, verifiable citations,
                    and evidence traceability.
        """
        raise NotImplementedError

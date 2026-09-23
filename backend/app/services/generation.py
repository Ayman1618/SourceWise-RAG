"""Pipeline interface and implementation for grounded answer generation and citation synthesis."""

import json
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.models.citation import Citation
from app.models.generation import Answer, EvidenceStatus
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


class GroundedGenerationService(BaseGenerationService):
    """Production service for generating factually grounded answers and verified citations."""

    REFUSAL_MESSAGE: str = (
        "I couldn't find sufficient supporting information in the available knowledge base to answer this reliably."
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        min_evidence_score: float | None = None,
        client: OpenAI | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the grounded generation service.

        Args:
            api_key: API key for the OpenAI-compatible provider (defaults to settings.llm_api_key).
            model: Model identifier (defaults to settings.llm_model).
            base_url: Base URL for OpenAI-compatible endpoint (defaults to settings.llm_base_url).
            temperature: Sampling temperature for generation (defaults to settings.llm_temperature).
            max_tokens: Maximum output tokens (defaults to settings.llm_max_tokens).
            min_evidence_score: Optional retrieval score threshold for pre-filtering low quality evidence.
            client: Optional pre-configured OpenAI client instance (useful for mocking/testing).
            **kwargs: Additional options forwarded to the client.
        """
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.min_evidence_score = (
            min_evidence_score if min_evidence_score is not None else settings.min_evidence_score
        )
        self._api_key = api_key or settings.llm_api_key
        self._base_url = base_url or settings.llm_base_url

        if client is not None:
            self.client = client
        else:
            effective_key = self._api_key or "mock-key-not-set"
            self.client = OpenAI(
                api_key=effective_key,
                base_url=self._base_url,
                **kwargs,
            )

    def _build_prompts(
        self,
        query: str,
        evidence: list[RetrievedChunk],
    ) -> tuple[str, str]:
        """Construct strict grounding system prompt and evidence-formatted user prompt."""
        system_prompt = (
            "You are SourceWise RAG, an evidence-first enterprise knowledge assistant.\n"
            "Your task is to answer the user's question accurately and objectively using ONLY the provided evidence chunks.\n\n"
            "CRITICAL GROUNDING RULES:\n"
            "1. Rely EXCLUSIVELY on the provided evidence passages. Do not use outside knowledge, assumptions, or unstated facts.\n"
            "2. Every factual assertion must be directly supported by the text in the provided chunks.\n"
            "3. Attribute statements by citing the specific chunk_id(s) of the evidence that directly supports them.\n"
            "4. If the provided evidence does not contain enough information to answer the question completely and reliably, "
            "or if the evidence is contradictory, set has_sufficient_evidence to false and set answer to: "
            f'"{self.REFUSAL_MESSAGE}"\n'
            "5. Never invent or hallucinate chunk IDs or document citations.\n\n"
            "RESPONSE FORMAT:\n"
            "You MUST respond in valid JSON matching this exact structure:\n"
            "{\n"
            '  "has_sufficient_evidence": true,\n'
            '  "answer": "Your comprehensive, grounded answer text here.",\n'
            '  "citations": [\n'
            "    {\n"
            '      "chunk_id": "exact_chunk_id_from_evidence",\n'
            '      "passage": "Exact excerpt from the chunk text supporting the claim"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        evidence_blocks: list[str] = []
        for rank, item in enumerate(evidence, start=1):
            title = item.chunk.metadata.get("title", item.document_id)
            source_path = item.chunk.metadata.get("source_path") or item.chunk.metadata.get("filepath", "")
            block = (
                f"[Evidence #{rank}]\n"
                f"Chunk ID: {item.chunk_id}\n"
                f"Document ID: {item.document_id}\n"
                f"Source Title: {title}\n"
            )
            if source_path:
                block += f"Source Path: {source_path}\n"
            block += f"Content:\n{item.text}"
            evidence_blocks.append(block)

        formatted_evidence = "\n\n---\n\n".join(evidence_blocks)

        user_prompt = (
            f"EVIDENCE PASSAGES:\n"
            f"----------------------------------------\n"
            f"{formatted_evidence}\n"
            f"----------------------------------------\n\n"
            f"USER QUESTION: {query}"
        )

        return system_prompt, user_prompt

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
            **kwargs: Additional generation options (e.g. model, temperature, max_tokens).

        Returns:
            Answer: Grounded response containing the answer text, verifiable citations,
                    and evidence sufficiency status.

        Raises:
            ValueError: If query is empty or whitespace only.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or whitespace only")

        # 1. Zero evidence check
        if not evidence:
            return Answer(
                query=query,
                answer=self.REFUSAL_MESSAGE,
                citations=[],
                evidence=[],
                evidence_status=EvidenceStatus.INSUFFICIENT,
                has_sufficient_evidence=False,
                confidence_score=0.0,
            )

        # 2. Optional retrieval score filtering
        effective_evidence = evidence
        if self.min_evidence_score > 0.0:
            effective_evidence = [e for e in evidence if e.score >= self.min_evidence_score]
            if not effective_evidence:
                return Answer(
                    query=query,
                    answer=self.REFUSAL_MESSAGE,
                    citations=[],
                    evidence=evidence,
                    evidence_status=EvidenceStatus.INSUFFICIENT,
                    has_sufficient_evidence=False,
                    confidence_score=0.0,
                )

        # Build chunk lookup map for fast verification
        chunk_map = {item.chunk_id: item for item in effective_evidence}

        # 3. Construct grounding prompt
        system_prompt, user_prompt = self._build_prompts(query, effective_evidence)

        # 4. Invoke LLM with structured JSON output
        model_name = kwargs.get("model", self.model)
        temp = kwargs.get("temperature", self.temperature)
        max_toks = kwargs.get("max_tokens", self.max_tokens)

        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temp,
            max_tokens=max_toks,
            response_format={"type": "json_object"},
        )

        response_content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(response_content)
        except json.JSONDecodeError:
            # If model response cannot be parsed as JSON, safely refuse
            return Answer(
                query=query,
                answer=self.REFUSAL_MESSAGE,
                citations=[],
                evidence=evidence,
                evidence_status=EvidenceStatus.REFUSED,
                has_sufficient_evidence=False,
                confidence_score=0.0,
            )

        has_sufficient = bool(parsed.get("has_sufficient_evidence", True))
        raw_answer = str(parsed.get("answer", "")).strip()
        raw_citations = parsed.get("citations", [])

        # 5. Handle model-determined insufficient evidence
        if not has_sufficient or raw_answer == self.REFUSAL_MESSAGE or not raw_answer:
            return Answer(
                query=query,
                answer=self.REFUSAL_MESSAGE,
                citations=[],
                evidence=evidence,
                evidence_status=EvidenceStatus.INSUFFICIENT,
                has_sufficient_evidence=False,
                confidence_score=0.0,
            )

        # 6. Validate citations and reject fabricated/invalid chunk IDs
        valid_citations: list[Citation] = []
        seen_chunk_ids: set[str] = set()

        if isinstance(raw_citations, list):
            for item in raw_citations:
                if not isinstance(item, dict):
                    continue
                chunk_id = str(item.get("chunk_id", "")).strip()

                # Strictly verify chunk_id exists in retrieved evidence
                if not chunk_id or chunk_id not in chunk_map:
                    # Invalid/hallucinated citation ID -> rejected
                    continue

                if chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(chunk_id)

                retrieved_chunk = chunk_map[chunk_id]
                source_title = (
                    retrieved_chunk.chunk.metadata.get("title")
                    or retrieved_chunk.document_id
                )
                source_path = (
                    retrieved_chunk.chunk.metadata.get("source_path")
                    or retrieved_chunk.chunk.metadata.get("filepath")
                )
                passage = str(item.get("passage", "")).strip() or retrieved_chunk.text

                citation = Citation(
                    citation_id=f"cite_{len(valid_citations) + 1}",
                    document_id=retrieved_chunk.document_id,
                    chunk_id=retrieved_chunk.chunk_id,
                    source_title=str(source_title),
                    passage=passage,
                    source_path=source_path,
                    score=retrieved_chunk.score,
                )
                valid_citations.append(citation)

        # 7. Verification: If model provided an answer but citations could not be validated
        if not valid_citations:
            # Evidence existed, but model response/citations could not be safely validated
            return Answer(
                query=query,
                answer=self.REFUSAL_MESSAGE,
                citations=[],
                evidence=evidence,
                evidence_status=EvidenceStatus.REFUSED,
                has_sufficient_evidence=False,
                confidence_score=0.0,
            )

        # Compute confidence score from cited chunks
        scores = [c.score for c in valid_citations if c.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 1.0

        return Answer(
            query=query,
            answer=raw_answer,
            citations=valid_citations,
            evidence=evidence,
            evidence_status=EvidenceStatus.SUFFICIENT,
            has_sufficient_evidence=True,
            confidence_score=round(avg_score, 4),
            metadata={
                "model": model_name,
                "citation_count": len(valid_citations),
            },
        )

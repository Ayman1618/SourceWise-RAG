"""Markdown-aware text chunking service for SourceWise RAG."""

from __future__ import annotations

import re
from typing import Any

from app.models.chunk import Chunk
from app.models.document import Document


class ChunkingService:
    """Segments normalized documents into discrete, traceable chunks.

    Adheres to:
    - Target chunk window: 500-800 tokens
    - Context overlap: 50-100 tokens
    - Semantic boundaries: markdown headers, paragraphs, code blocks
    - Deterministic chunk IDs: {document_id}#chunk_{chunk_index}
    - Parent lineage preservation: document_id, source metadata
    """

    def __init__(
        self,
        min_chunk_tokens: int = 500,
        max_chunk_tokens: int = 800,
        overlap_tokens: int = 75,
    ) -> None:
        """Initialize the chunking service with token boundary configurations.

        Args:
            min_chunk_tokens: Minimum target tokens before allowing heading splits (default: 500).
            max_chunk_tokens: Maximum target tokens per chunk (default: 800).
            overlap_tokens: Target token count for overlap between consecutive chunks (default: 75).
        """
        if min_chunk_tokens <= 0 or max_chunk_tokens <= 0:
            raise ValueError("Token limits must be positive integers")
        if min_chunk_tokens > max_chunk_tokens:
            raise ValueError("min_chunk_tokens cannot exceed max_chunk_tokens")
        if overlap_tokens < 0 or overlap_tokens >= max_chunk_tokens:
            raise ValueError("overlap_tokens must be non-negative and strictly less than max_chunk_tokens")

        self.min_chunk_tokens = min_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text using word and punctuation boundary tokens.

        Matches BPE tokenizer distribution closely for technical Markdown without external API calls.
        """
        if not text or not text.strip():
            return 0
        tokens = re.findall(r"\w+|[^\w\s]", text)
        return max(1, len(tokens))

    def chunk_document(
        self,
        document: Document,
        min_chunk_tokens: int | None = None,
        max_chunk_tokens: int | None = None,
        overlap_tokens: int | None = None,
    ) -> list[Chunk]:
        """Split a normalized Document into discrete Chunk objects.

        Args:
            document: Canonical Document object to segment.
            min_chunk_tokens: Optional per-invocation override for min tokens.
            max_chunk_tokens: Optional per-invocation override for max tokens.
            overlap_tokens: Optional per-invocation override for overlap tokens.

        Returns:
            list[Chunk]: Traceable chunks with inherited metadata and deterministic IDs.
        """
        min_tokens = min_chunk_tokens or self.min_chunk_tokens
        max_tokens = max_chunk_tokens or self.max_chunk_tokens
        overlap = overlap_tokens if overlap_tokens is not None else self.overlap_tokens

        text_chunks = self._chunk_text(
            text=document.content,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            overlap_tokens=overlap,
        )

        inherited_metadata: dict[str, Any] = {
            "document_id": document.document_id,
            "title": document.title,
            "source_path": document.source_path,
            "source_type": document.source_type,
            "product": document.product,
            "version": document.version,
            "department": document.department,
            "owner": document.owner,
            "access_level": document.access_level,
            "language": document.language,
            "last_updated": str(document.last_updated) if document.last_updated is not None else None,
            **document.metadata,
        }

        chunks: list[Chunk] = []
        for index, chunk_text in enumerate(text_chunks):
            chunk_id = f"{document.document_id}#chunk_{index}"
            token_count = self.count_tokens(chunk_text)

            chunk = Chunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                text=chunk_text,
                chunk_index=index,
                token_count=token_count,
                metadata={
                    **inherited_metadata,
                    "document_id": document.document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": index,
                },
            )
            chunks.append(chunk)

        return chunks

    def _chunk_text(
        self,
        text: str,
        min_tokens: int,
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[str]:
        """Segment raw text into string chunks respecting Markdown boundaries and overlap."""
        raw_blocks = self._split_into_semantic_blocks(text)
        if not raw_blocks:
            return []

        # Ensure no individual block exceeds max_tokens
        blocks: list[str] = []
        for block in raw_blocks:
            if self.count_tokens(block) > max_tokens:
                sub_blocks = self._subdivide_large_block(block, max_tokens)
                blocks.extend(sub_blocks)
            else:
                blocks.append(block)

        chunks: list[str] = []
        current_blocks: list[str] = []
        current_tokens = 0

        for block in blocks:
            block_tokens = self.count_tokens(block)
            is_major_heading = bool(re.match(r"^#{1,3}\s+", block.strip()))

            # Check boundary condition:
            # 1. Block pushes chunk beyond max_tokens
            # 2. Or chunk has already met min_tokens and encounters a section heading
            if current_blocks and (
                (current_tokens + block_tokens > max_tokens)
                or (current_tokens >= min_tokens and is_major_heading)
            ):
                chunk_text = "\n\n".join(current_blocks).strip()
                chunks.append(chunk_text)

                if overlap_tokens > 0:
                    overlap_text = self._extract_overlap(chunk_text, overlap_tokens)
                    current_blocks = [overlap_text, block] if overlap_text else [block]
                else:
                    current_blocks = [block]

                current_tokens = sum(self.count_tokens(b) for b in current_blocks)
            else:
                current_blocks.append(block)
                current_tokens += block_tokens

        if current_blocks:
            chunk_text = "\n\n".join(current_blocks).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks

    def _split_into_semantic_blocks(self, text: str) -> list[str]:
        """Split markdown text into logical units: headings, paragraphs, code blocks, tables."""
        lines = text.splitlines()
        blocks: list[str] = []
        current_lines: list[str] = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()

            # Handle code block fences
            if stripped.startswith("```"):
                if in_code_block:
                    current_lines.append(line)
                    blocks.append("\n".join(current_lines))
                    current_lines = []
                    in_code_block = False
                    continue
                else:
                    if current_lines:
                        blocks.append("\n".join(current_lines))
                        current_lines = []
                    in_code_block = True
                    current_lines.append(line)
                    continue

            if in_code_block:
                current_lines.append(line)
                continue

            # Markdown headings
            if re.match(r"^#{1,6}\s+", stripped):
                if current_lines:
                    blocks.append("\n".join(current_lines))
                    current_lines = []
                current_lines.append(line)
                continue

            # Horizontal rules
            if stripped in ("---", "***", "___"):
                if current_lines:
                    blocks.append("\n".join(current_lines))
                    current_lines = []
                continue

            # Empty lines delineate paragraphs
            if not stripped:
                if current_lines:
                    blocks.append("\n".join(current_lines))
                    current_lines = []
                continue

            current_lines.append(line)

        if current_lines:
            blocks.append("\n".join(current_lines))

        return [b.strip() for b in blocks if b.strip()]

    def _subdivide_large_block(self, block: str, max_tokens: int) -> list[str]:
        """Subdivide an oversized atomic block into smaller sentence-level or line-level chunks."""
        # Check if it is a fenced code block
        if block.startswith("```") and block.endswith("```"):
            inner_lines = block.splitlines()
            result: list[str] = []
            cur: list[str] = []
            cur_tokens = 0
            for line in inner_lines:
                lt = self.count_tokens(line)
                if cur and (cur_tokens + lt > max_tokens):
                    result.append("\n".join(cur))
                    cur = [line]
                    cur_tokens = lt
                else:
                    cur.append(line)
                    cur_tokens += lt
            if cur:
                result.append("\n".join(cur))
            return result

        # Split regular block by sentence boundaries
        sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", block) if s.strip()]
        result: list[str] = []
        cur_sentences: list[str] = []
        cur_tokens = 0

        for sentence in sentences:
            st = self.count_tokens(sentence)
            if cur_sentences and (cur_tokens + st > max_tokens):
                result.append(" ".join(cur_sentences))
                cur_sentences = [sentence]
                cur_tokens = st
            else:
                cur_sentences.append(sentence)
                cur_tokens += st

        if cur_sentences:
            result.append(" ".join(cur_sentences))

        return result

    def _extract_overlap(
        self,
        text: str,
        target_overlap_tokens: int,
        min_overlap_tokens: int = 50,
        max_overlap_tokens: int = 100,
    ) -> str:
        """Extract a trailing slice of sentences/lines from text matching target overlap token count.

        Targets approximately 50-100 tokens of overlap across sentence boundaries.
        """
        sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", text) if s.strip()]
        selected: list[str] = []
        current_tokens = 0

        for sentence in reversed(sentences):
            st = self.count_tokens(sentence)
            if current_tokens + st > max_overlap_tokens and selected and current_tokens >= min_overlap_tokens:
                break
            selected.insert(0, sentence)
            current_tokens += st
            if current_tokens >= target_overlap_tokens and current_tokens >= min_overlap_tokens:
                break

        return " ".join(selected).strip()


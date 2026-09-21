"""Markdown parser and frontmatter extractor for SourceWise RAG."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import yaml

from app.models.document import Document


class MarkdownParseError(ValueError):
    """Raised when markdown source or frontmatter is malformed or invalid."""


class MarkdownParser:
    """Parses raw Markdown documents with optional YAML frontmatter into canonical Document objects."""

    _FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?",
        re.DOTALL,
    )
    _FIRST_HEADING_PATTERN = re.compile(
        r"^#\s+(.+)$",
        re.MULTILINE,
    )

    KNOWN_DOCUMENT_FIELDS = {
        "document_id",
        "title",
        "content",
        "source_type",
        "source_path",
        "product",
        "version",
        "department",
        "owner",
        "last_updated",
        "access_level",
        "language",
        "metadata",
    }

    def parse(
        self,
        raw_text: str,
        source_path: str | Path | None = None,
        default_source_type: str = "product_documentation",
    ) -> Document:
        """Parse raw markdown text, extract metadata and content, and return a normalized Document.

        Args:
            raw_text: Raw markdown text content including optional frontmatter.
            source_path: Optional file path or URI of the document.
            default_source_type: Fallback source_type if not specified in frontmatter.

        Returns:
            Document: Normalized Document model instance.

        Raises:
            MarkdownParseError: If frontmatter is syntactically invalid or content is empty.
        """
        if not raw_text or not raw_text.strip():
            raise MarkdownParseError("Document text cannot be empty or whitespace only")

        path_obj = Path(source_path) if source_path else None
        normalized_source_path = str(path_obj).replace("\\", "/") if path_obj else None

        frontmatter: dict[str, Any] = {}
        body = raw_text

        # Extract frontmatter if present
        match = self._FRONTMATTER_PATTERN.match(raw_text)
        if match:
            fm_text = match.group(1)
            body = raw_text[match.end():]
            try:
                loaded = yaml.safe_load(fm_text)
                if loaded is not None:
                    if not isinstance(loaded, dict):
                        raise MarkdownParseError("Frontmatter must be a YAML key-value mapping")
                    frontmatter = loaded
            except yaml.YAMLError as exc:
                raise MarkdownParseError(f"Malformed YAML frontmatter: {exc}") from exc
        elif raw_text.startswith("---"):
            # Opening delimiter present but no closing delimiter found
            raise MarkdownParseError("Malformed frontmatter: missing closing '---' delimiter")

        clean_body = body.strip()
        if not clean_body:
            raise MarkdownParseError("Document body content cannot be empty")

        # Resolve document title
        title = self._resolve_title(frontmatter, clean_body, path_obj)

        # Resolve document ID
        document_id = self._resolve_document_id(frontmatter, title, path_obj)

        # Resolve source type
        source_type = frontmatter.get("source_type") or default_source_type

        # Partition known Document fields vs custom metadata
        custom_metadata: dict[str, Any] = {}
        if isinstance(frontmatter.get("metadata"), dict):
            custom_metadata.update(frontmatter["metadata"])

        for key, value in frontmatter.items():
            if key not in self.KNOWN_DOCUMENT_FIELDS:
                custom_metadata[key] = value

        doc_payload: dict[str, Any] = {
            "document_id": document_id,
            "title": title,
            "content": clean_body,
            "source_type": str(source_type),
            "source_path": normalized_source_path or frontmatter.get("source_path"),
            "product": frontmatter.get("product"),
            "version": str(frontmatter["version"]) if "version" in frontmatter and frontmatter["version"] is not None else None,
            "department": frontmatter.get("department"),
            "owner": frontmatter.get("owner"),
            "last_updated": frontmatter.get("last_updated"),
            "access_level": frontmatter.get("access_level", "internal"),
            "language": frontmatter.get("language", "en"),
            "metadata": custom_metadata,
        }

        try:
            return Document(**doc_payload)
        except Exception as exc:
            raise MarkdownParseError(f"Failed to create Document from parsed payload: {exc}") from exc

    def parse_file(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        default_source_type: str = "product_documentation",
    ) -> Document:
        """Read and parse a Markdown file from the local filesystem.

        Args:
            file_path: Path to the markdown file.
            encoding: Text encoding (default: utf-8).
            default_source_type: Fallback source_type.

        Returns:
            Document: Normalized Document model instance.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        raw_text = path.read_text(encoding=encoding)
        return self.parse(
            raw_text=raw_text,
            source_path=path,
            default_source_type=default_source_type,
        )

    def _resolve_title(
        self,
        frontmatter: dict[str, Any],
        body: str,
        path: Path | None,
    ) -> str:
        """Determine document title using frontmatter, first # heading, or filename fallback."""
        fm_title = frontmatter.get("title")
        if fm_title and str(fm_title).strip():
            return str(fm_title).strip()

        # Try first markdown H1
        h1_match = self._FIRST_HEADING_PATTERN.search(body)
        if h1_match:
            heading = h1_match.group(1).strip()
            if heading:
                return heading

        # Fallback to path stem
        if path:
            return path.stem.replace("-", " ").replace("_", " ").title()

        return "Untitled Document"

    def _resolve_document_id(
        self,
        frontmatter: dict[str, Any],
        title: str,
        path: Path | None,
    ) -> str:
        """Determine document ID from frontmatter, path slug, or title slug."""
        fm_id = frontmatter.get("document_id")
        if fm_id and str(fm_id).strip():
            clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(fm_id).strip())
            return clean_id

        if path:
            clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", path.stem.strip())
            return clean_id.lower()

        clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", title.strip().lower())
        return clean_slug.strip("_") or "document"

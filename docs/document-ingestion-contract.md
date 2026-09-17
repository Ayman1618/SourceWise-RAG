# Document Ingestion Contract

## 1. Purpose of the Contract

The **Document Ingestion Contract** defines the canonical data representation for documents entering the SourceWise RAG pipeline.

Before knowledge documents can be parsed, cleaned, segmented into chunks, embedded into vector representations, and indexed in vector search systems (e.g., Qdrant), they must adhere to a predictable and standardized document schema.

```text
Raw Source (Markdown, Wiki, Ticket)
               │
               ▼
   [Normalization / Ingestion]
               │
               ▼
   Canonical Document Representation (This Contract)
               │
               ▼
   [Chunking & Segmentation]
               │
               ▼
   Child Chunk Representation (Preserving document_id)
               │
               ▼
   [Embedding & Vector Indexing]
```

This contract establishes:
1. **Predictability**: Consistent attributes across disparate knowledge sources (wikis, support tickets, guides, release notes).
2. **Grounding & Traceability**: Immutable lineage from source documents down to segmented chunks and citations.
3. **Citation Readiness**: Sufficient contextual metadata (`title`, `source_path`, `version`, `owner`) to generate human-verifiable citations in the user interface.
4. **Access Control & Filtering**: Granular classification (`access_level`, `product`, `department`) to support pre-retrieval filtering.

> **Note**: This document specifies a conceptual and architectural contract. It does not implement ingestion code, parsers, database schemas, or validation libraries in this phase.

---

## 2. Canonical Document Representation

A normalized document in SourceWise RAG is conceptually structured as follows:

```json
{
  "document_id": "sample-authentication-guide",
  "title": "Product Authentication Guide",
  "source_type": "product_documentation",
  "product": "SourceWise Platform",
  "version": "1.0",
  "department": "Engineering",
  "owner": "Platform Engineering",
  "last_updated": "2026-09-15",
  "access_level": "internal",
  "language": "en",
  "source_path": "data/sample-documents/product-authentication-guide.md",
  "content": "Normalized document text"
}
```

---

## 3. Schema Fields Specification

### 3.1 Required Fields

These fields are strictly mandatory. Any source document lacking one of these fields cannot be ingested:

| Field Name | Type | Description | Validation Constraints |
| :--- | :--- | :--- | :--- |
| `document_id` | `string` | Unique identifier for the document across the entire knowledge base. | Non-empty, ASCII alphanumeric + hyphens/underscores (`^[a-zA-Z0-9_-]+$`). |
| `title` | `string` | Human-readable title or document heading. | Non-empty, single-line, trimmed whitespace. |
| `source_type` | `string` | Classification category of the source content. | Must be one of the supported source types (see Section 4). |
| `content` | `string` | Full normalized textual body of the document. | Non-empty string; stripped of raw binary artifacts. |

### 3.2 Optional / Contextual Fields

These fields enrich retrieval, citation rendering, and permission management:

| Field Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `source_path` | `string \| null` | `null` | File system path, repository path, or URL pointing to the original source. |
| `product` | `string \| null` | `null` | Name of the product, subsystem, or platform to which the document applies. |
| `version` | `string \| null` | `null` | Document or software version identifier (e.g., `"1.0"`, `"2.1.4"`). |
| `department` | `string \| null` | `null` | Business or engineering division owning the document (e.g., `"Engineering"`). |
| `owner` | `string \| null` | `null` | Individual author, email, or team responsible for the content. |
| `last_updated` | `string \| null` | `null` | ISO-8601 date string representing the document's last revision date. |
| `access_level` | `string` | `"internal"` | Data classification level (`"public"`, `"internal"`, `"confidential"`, `"restricted"`). |
| `language` | `string` | `"en"` | Two-letter ISO 639-1 language code. |
| `metadata` | `object` | `{}` | Key-value dictionary for source-specific attributes (e.g., ticket ID, tags, external URLs). |

---

## 4. Supported Source Types

The `source_type` field dictates downstream extraction heuristics, chunking strategies, and UI badge rendering.

The supported standard values include:

| `source_type` | Intended Usage | Example Sources |
| :--- | :--- | :--- |
| `product_documentation` | Formal user-facing or internal product guides and manuals. | Integration guides, API references, feature manuals. |
| `support_ticket` | Resolved customer or internal IT support resolutions. | Zendesk/Jira service desk issue resolutions. |
| `engineering_wiki` | Internal architecture, engineering specifications, and designs. | Confluence specs, internal RFCs, system designs. |
| `troubleshooting_guide` | Diagnostic procedures, error recovery runbooks, and SOPs. | On-call playbooks, login triage guides. |
| `release_note` | Changelogs, version updates, and feature deprecation notices. | Monthly release announcements, upgrade notes. |
| `faq` | Curated frequently asked questions with direct Q&A pairs. | Customer help centers, internal onboarding FAQs. |

*Note: This vocabulary will be expanded as additional source connectors (e.g., Slack threads, legal policies) are added in future milestones.*

---

## 5. Metadata Rules and Conventions

### 5.1 Document ID Rules
1. **Uniqueness**: `document_id` must be globally unique within a knowledge base partition.
2. **Format**: Must use lowercase alphanumeric characters, dashes, or underscores (`sample-authentication-guide`, `kb_doc_1042`).
3. **Determinism**: For file-based sources, `document_id` should ideally be derived deterministically from the relative path or file slug, ensuring idempotency across re-ingestion runs.
4. **Immutability**: Once assigned, `document_id` must never change across document revisions; version increments should be handled via the `version` attribute or revision metadata.

### 5.2 Source Traceability & Downstream Chunk Inheritance
To guarantee full lineage and groundability:
* Every downstream **Chunk** generated during segmentation must retain a direct reference to the parent document:
  ```text
  Chunk.document_id == Document.document_id
  ```
* Chunks must also inherit `title`, `source_path`, `version`, and `access_level` to facilitate immediate citation assembly without requiring secondary database joins during retrieval.
* Citations rendered in responses will format references as:
  ```text
  [Title, vVersion (source_path)]
  ```

### 5.3 Rules for Missing Metadata
1. If an optional string field is omitted in the source document, it defaults to `null` (or its documented default, such as `access_level: "internal"`, `language: "en"`).
2. Ingestion pipelines should not invent synthetic values for missing factual fields (`product`, `version`, `department`, `owner`); leave them as `null` to avoid hallucinated metadata.
3. If `title` is missing from frontmatter, an extraction rule should attempt to infer it from the first top-level Markdown heading (`# Heading`). If no heading exists, the source file slug may be used as a fallback.

### 5.4 Rules for Version and Date Values
1. **Dates (`last_updated`)**: Must conform strictly to ISO-8601 calendar date (`YYYY-MM-DD`) or timestamp (`YYYY-MM-DDTHH:MM:SSZ`) format. Unstructured strings like `"last Tuesday"` or `"September 2026"` are invalid.
2. **Versions (`version`)**: Should follow Semantic Versioning (`MAJOR.MINOR.PATCH`) or standard enterprise release designations (e.g., `"1.0"`, `"2.4.1"`, `"v2026.3"`).

---

## 6. Example Representation

### 6.1 Source Frontmatter (Markdown Source)
```markdown
---
document_id: sample-authentication-guide
title: Product Authentication Guide
source_type: product_documentation
product: SourceWise Platform
version: "1.0"
department: Engineering
owner: Platform Engineering
last_updated: "2026-09-15"
access_level: internal
language: en
---

# Product Authentication Guide
...
```

### 6.2 Normalized Document Object
```json
{
  "document_id": "sample-authentication-guide",
  "title": "Product Authentication Guide",
  "source_type": "product_documentation",
  "product": "SourceWise Platform",
  "version": "1.0",
  "department": "Engineering",
  "owner": "Platform Engineering",
  "last_updated": "2026-09-15",
  "access_level": "internal",
  "language": "en",
  "source_path": "data/sample-documents/product-authentication-guide.md",
  "content": "# Product Authentication Guide\n\n## Summary\nThis guide outlines the authentication architecture..."
}
```

---

## 7. Next Steps in Document Pipeline

This document establishes the contract boundary for the data engineering pipeline. Subsequent PRs will build upon this contract:
1. **Document Parsers**: Extracting YAML frontmatter and body content into normalized in-memory structures.
2. **Chunking Engine**: Splitting normalized document content into discrete, context-aware segments while embedding parent `document_id` references.
3. **Vector Ingestion**: Embedding chunks and persisting vectors alongside metadata payloads into Qdrant.

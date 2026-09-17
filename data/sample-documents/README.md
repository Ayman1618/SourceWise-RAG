# Sample Documents

## Overview

This directory contains synthetic, non-sensitive sample enterprise documents created specifically for local development, pipeline testing, and evaluation within SourceWise RAG.

---

## Important Notice

* **Synthetic Data Only**: All content, employee names, system configurations, endpoints, policy rules, and organizational structures contained in these documents are completely fictional.
* **No Confidential Information**: None of these files contain real credentials, API tokens, internal corporate secrets, proprietary source code, or personally identifiable information (PII).
* **Local Development & Testing**: These documents are intended solely for testing the ingestion, chunking, embedding, vector retrieval, and grounding evaluation flows locally and in automated test suites.

---

## Document Collection

The sample document corpus consists of:

| File | Document ID | Source Type | Owner | Description |
| :--- | :--- | :--- | :--- | :--- |
| [`product-authentication-guide.md`](./product-authentication-guide.md) | `sample-authentication-guide` | `product_documentation` | Platform Engineering | Architecture, OAuth 2.0 / OIDC flows, API keys, MFA, and SSO configuration. |
| [`support-login-troubleshooting.md`](./support-login-troubleshooting.md) | `sample-login-troubleshooting` | `troubleshooting_guide` | Support Operations | Step-by-step triage for authentication failures, account lockouts, and MFA desync. |
| [`api-rate-limits.md`](./api-rate-limits.md) | `sample-api-rate-limits` | `product_documentation` | API Infrastructure | Token bucket algorithms, tier quotas, HTTP 429 response handling, and exemption SLAs. |

---

## Test Suitability and Chunking Characteristics

Each document in this collection has been authored to reflect realistic enterprise documentation standards:
* **Rich Structure**: Features distinct sections, nested headers, bulleted lists, and structured tables.
* **Granular Facts**: Contains unambiguous factual statements, exact error codes, rate limit figures, and step-by-step procedures designed to test retrieval precision.
* **Multi-Chunk Volume**: Each document has sufficient depth and length (typically 1,000–2,500 words) to produce multiple meaningful chunks (4–10 chunks per document at standard 300–500 token window sizes), enabling effective verification of:
  * Chunk boundary handling and semantic coherence
  * Heading and context preservation across adjacent chunks
  * Cross-chunk retrieval and synthesis
  * Accurate chunk-level citation mapping back to parent documents

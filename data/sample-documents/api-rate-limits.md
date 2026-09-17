---
document_id: sample-api-rate-limits
title: API Rate Limits and Quota Management
source_type: product_documentation
product: SourceWise Platform
version: "2.0"
department: Engineering
owner: API Infrastructure Team
last_updated: "2026-09-14"
access_level: internal
language: en
---

# API Rate Limits and Quota Management

## Summary
This document specifies the rate limiting policies, sliding window algorithms, response headers, error codes, and quota increase request processes for the SourceWise Platform APIs. It ensures platform availability, protects vector indexing and retrieval backends from load surges, and provides clear integration guidelines for client developers.

---

## 1. Rate Limiting Architecture

SourceWise APIs employ a distributed **Token Bucket algorithm** executed by the Edge Gateway and backed by clustered Redis instances.

```text
[Client Request] ──> [Edge Gateway (Rate Limiter)] ──(Token Available?)
                                                            ├── YES ──> [Service Handlers]
                                                            └── NO  ──> [HTTP 429 Response]
```

### Key Properties
* **Evaluation Windows**: Rate limits are calculated across 60-second rolling intervals and 24-hour calendar days (UTC).
* **Identification Keys**:
  * Authenticated requests: Tracked by `api_key_id` or authenticated user UUID (`sub` claim).
  * Anonymous / Pre-auth endpoints: Tracked by client source IP address (`X-Forwarded-For`).
* **Burst Allowance**: Clients may burst up to 20% over per-minute limits for durations under 5 consecutive seconds before requests are throttled.

---

## 2. Standard Tier Quotas

The following limits apply to all public and internal REST/gRPC endpoints:

| Subscription Tier | Requests / Min | Daily Cap (Req / 24h) | Concurrent Streaming Queries | Batch Ingestion Limit |
| :--- | :--- | :--- | :--- | :--- |
| **Starter / Sandbox** | 60 | 2,000 | 2 | 10 docs / request |
| **Professional** | 300 | 25,000 | 10 | 50 docs / request |
| **Enterprise** | 1,200 | 250,000 | 50 | 250 docs / request |
| **Internal Microservices** | 6,000 | Unlimited | 200 | 1,000 docs / request |

*Note: Heavy endpoints such as `/v1/rag/query` and `/v1/documents/embed` consume 2 tokens per invocation due to compute intensity.*

---

## 3. Rate Limit Response Headers

Every HTTP response returned by SourceWise APIs includes standardized tracking headers:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 284
X-RateLimit-Reset: 1789471560
Retry-After: 0
```

### Header Definitions
* `X-RateLimit-Limit`: Maximum requests permitted within the current rolling window.
* `X-RateLimit-Remaining`: Remaining request allowance in the current window.
* `X-RateLimit-Reset`: Unix epoch timestamp (in seconds) indicating when the current window quota replenishes.
* `Retry-After`: Number of seconds the client must wait before making another request (only present on HTTP 429 responses).

---

## 4. Handling HTTP 429 (Too Many Requests)

When a client exhausts its quota, the API responds with HTTP 429 and a JSON error envelope:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Quota limit of 300 requests per minute exceeded.",
    "tier": "Professional",
    "retry_after_seconds": 24,
    "reset_timestamp": 1789471560
  }
}
```

### Client Implementation Best Practices
1. **Exponential Backoff with Full Jitter**:
   Implement retry loops that compute wait time with randomized jitter:
   $$\text{WaitTime} = \min(\text{MaxBackoff}, \text{BaseDelay} \times 2^{\text{attempt}}) \times \text{random}(0.5, 1.5)$$
2. **Observe `Retry-After`**: Never retry sooner than the duration provided in the `Retry-After` response header.
3. **Connection Pooling & Batching**: Group multiple document uploads into single batch requests (`/v1/documents/batch`) rather than submitting individual document requests.
4. **Local Response Caching**: Cache semantic search responses using client-side TTL caches (e.g., 5–15 minutes) for frequent or identical queries.

---

## 5. Quota Increase and Exemption Process

Clients requiring sustained throughput exceeding standard tier ceilings may submit a quota increase request.

### 5.1 Request Criteria
* System architecture must already implement exponential backoff and connection pooling.
* Justification must include projected peak QPS, estimated daily query volumes, and business rationale.

### 5.2 Submission Workflow
1. Navigate to **Developer Console → API Keys → Manage Quotas → Request Limit Increase**.
2. Complete the technical evaluation questionnaire.
3. Review SLA and turnaround:
   * **Professional Tier**: Reviewed within 2 business days; approval up to $2\times$ standard tier.
   * **Enterprise Tier**: Reviewed within 4 business hours; custom scaling plans coordinated with API Infrastructure Team.

---

## 6. Technical Troubleshooting

Common rate-limiting issues and remediation steps:

| Problem Observed | Common Root Cause | Remediation |
| :--- | :--- | :--- |
| **Premature 429 on Unauthenticated Route** | Multiple developers or CI runners sharing a single NAT public IP. | Use distinct API Keys for each runner or authenticate before querying. |
| **Double Rate Deduction** | Calling high-compute endpoints (`/rag/query`, `/embed`) without accounting for 2-token weight. | Plan client capacity around weighted endpoint costs. |
| **Sudden Spike in Ingestion 429s** | Ingestion worker threads submitting individual docs concurrently without thread pools. | Switch to `/v1/documents/batch` endpoint and bound concurrency to 5 workers. |
| **Burst Throttling** | Sending large bursts of requests at the start of a minute window. | Implement client-side token bucket or leaky bucket smoothing. |

---

## 7. Related Information

* [Product Authentication Guide](./product-authentication-guide.md) (`sample-authentication-guide`)
* [Support Login Troubleshooting Guide](./support-login-troubleshooting.md) (`sample-login-troubleshooting`)
* [Document Ingestion Contract](../../docs/document-ingestion-contract.md)

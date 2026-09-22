export type SourceType =
  | "Support Documentation"
  | "Engineering Specification"
  | "Developer Reference"
  | "Operations Runbook"
  | "Regulatory Standard";

export interface KnowledgeDocument {
  id: string;
  slug: string;
  title: string;
  summary: string;
  content: string;
  sourceType: SourceType;
  product: string;
  version: string;
  lastUpdated: string;
  department: string;
  author: string;
  tags: string[];
  chunkCount: number;
}

export const KNOWLEDGE_DOCUMENTS: KnowledgeDocument[] = [
  {
    id: "DOC-2024-881",
    slug: "support-login-troubleshooting",
    title: "Support Login Troubleshooting Guide",
    summary:
      "Step-by-step resolution protocol for user authentication failures, account lockouts, session timeouts, and MFA reset procedures.",
    sourceType: "Support Documentation",
    product: "Authentication & Access",
    version: "v2.1",
    lastUpdated: "2026-09-15",
    department: "Support Operations",
    author: "Elena Rostova",
    tags: ["login", "authentication", "lockout", "mfa", "troubleshooting", "session"],
    chunkCount: 14,
    content: `
# Support Login Troubleshooting Guide

## Overview
This document provides standard operating procedures for resolving user authentication issues within enterprise applications connected to the central IAM portal.

## Common Issue Categories

### 1. Account Lockout
Accounts are automatically locked after 5 consecutive failed login attempts within a 15-minute window.
- **Symptom**: User sees "Account temporarily locked due to multiple failed attempts."
- **Resolution**: Verify user identity via primary email or manager approval, then invoke reset in IAM Console or wait for the 15-minute automated lockout timer to expire.

### 2. Expired Session Tokens
Session tokens expire after 8 hours of inactivity or 24 hours total duration.
- **Symptom**: User is redirected to login page mid-session with HTTP 401 Unauthorized.
- **Resolution**: Advise user to clear browser session storage or re-authenticate through SSO portal.

### 3. Multi-Factor Authentication (MFA) Desynchronization
- **Symptom**: TOTP code is rejected despite correct input.
- **Resolution**: Perform a time synchronization check on the authenticator app or issue a temporary emergency bypass code valid for 1 hour.
    `.trim(),
  },
  {
    id: "DOC-2024-412",
    slug: "product-authentication-guide",
    title: "Product Authentication & IAM Protocol Guide",
    summary:
      "Technical specification detailing OAuth2/OIDC token flows, JWT validation rules, scope definitions, and identity provider integration standards.",
    sourceType: "Engineering Specification",
    product: "Security Standards",
    version: "v1.4",
    lastUpdated: "2026-09-12",
    department: "Security Architecture",
    author: "Marcus Vance",
    tags: ["oauth2", "oidc", "jwt", "iam", "security", "tokens"],
    chunkCount: 22,
    content: `
# Product Authentication & IAM Protocol Guide

## OAuth2 & OpenID Connect Implementation
All client microservices must authenticate against the central Identity Provider using standard OAuth2 Authorization Code Flow with PKCE.

## JWT Validation Requirements
API Gateway services MUST validate incoming Bearer tokens using RS256 public key verification:
1. Verify signature against published JWKS endpoint (\`/well-known/jwks.json\`).
2. Verify token claim \`iss\` matches \`https://auth.enterprise.internal\`.
3. Verify \`aud\` claim includes the specific target service API identifier.
4. Reject expired tokens where \`exp < current_timestamp\`.

## Scopes and Claims
- \`openid\`: Standard user sub identity
- \`profile\`: Display name and department
- \`read:docs\`: Enterprise documentation query permissions
- \`admin:ingest\`: Knowledge base document ingestion rights
    `.trim(),
  },
  {
    id: "DOC-2024-309",
    slug: "api-rate-limits",
    title: "API Rate Limits & Quota Specifications",
    summary:
      "Enterprise API rate limit guidelines, sliding window throttling rules, header specifications (X-RateLimit-Remaining), and tier allocations.",
    sourceType: "Developer Reference",
    product: "Platform APIs",
    version: "v3.0",
    lastUpdated: "2026-09-10",
    department: "Platform Engineering",
    author: "Siddharth Nair",
    tags: ["api", "rate-limits", "throttling", "quotas", "headers", "gateway"],
    chunkCount: 18,
    content: `
# API Rate Limits & Quota Specifications

## Global Throttling Policy
To ensure high availability, API Gateway enforces rate limiting using a token bucket algorithm with sliding window counters.

## Rate Limit Tiers

| Tier | Request Limit | Window | Burst Limit |
|---|---|---|---|
| Basic Developer | 100 req | 1 minute | 150 req |
| Standard Business | 1,000 req | 1 minute | 1,500 req |
| Enterprise Service | 10,000 req | 1 minute | 15,000 req |

## HTTP Response Headers
All API responses include standard rate limit status headers:
- \`X-RateLimit-Limit\`: Maximum allowed requests in window
- \`X-RateLimit-Remaining\`: Remaining capacity in current window
- \`X-RateLimit-Reset\`: UTC epoch timestamp when rate limit resets
- \`HTTP 429 Too Many Requests\`: Returned when bucket capacity is exhausted
    `.trim(),
  },
  {
    id: "DOC-2024-650",
    slug: "database-failover-runbook",
    title: "Emergency Database Failover & Recovery Runbook",
    summary:
      "Operational runbook for primary database failover, automated replica promotion, connection pool failover, and data integrity verification.",
    sourceType: "Operations Runbook",
    product: "Infrastructure & Core",
    version: "v1.8",
    lastUpdated: "2026-09-08",
    department: "Site Reliability Engineering",
    author: "Sarah Jenkins",
    tags: ["database", "postgres", "failover", "sre", "runbook", "high-availability"],
    chunkCount: 16,
    content: `
# Emergency Database Failover & Recovery Runbook

## Scope & Trigger Conditions
This runbook applies to primary PostgreSQL cluster unreachability exceeding 30 seconds or disk I/O failure alerts.

## Emergency Failover Procedure

### Step 1: Confirm Primary Unavailability
Execute check script:
\`\`\`bash
sre-cli db check --cluster primary-us-east
\`\`\`

### Step 2: Promote Standby Replica
If primary is unresponsive, trigger manual promotion on standby-01:
\`\`\`bash
pg_ctl promote -D /var/lib/postgresql/data
\`\`\`

### Step 3: Update Connection Pool Routing
Update PgBouncer VIP routing or update Route53 DNS record \`db-primary.internal\` to point to standby-01 IP.

### Step 4: Verify Transaction Consistency
Check replication lag metrics and confirm zero split-brain scenarios before declaring operational recovery.
    `.trim(),
  },
  {
    id: "DOC-2024-115",
    slug: "data-retention-compliance",
    title: "Customer Data Retention & Privacy Compliance Standard",
    summary:
      "Enterprise compliance policy governing data retention schedules, PII sanitization, document deletion logs, and audit trail retention.",
    sourceType: "Regulatory Standard",
    product: "Legal & Compliance",
    version: "v2.0",
    lastUpdated: "2026-09-01",
    department: "Information Governance",
    author: "David Chen",
    tags: ["compliance", "privacy", "gdpr", "retention", "pii", "audit"],
    chunkCount: 12,
    content: `
# Customer Data Retention & Privacy Compliance Standard

## Policy Scope
Applies to all enterprise data stores, vector indexes, document storage buckets, and cached log aggregation systems.

## Mandatory Retention Schedules
- **Customer Support Logs**: 90 days after ticket resolution
- **Authentication Logs**: 365 days for audit compliance
- **Vector Search Document Embeddings**: Retained until parent source document deletion
- **Audit Logs**: 7 years immutable storage in Write-Once-Read-Many (WORM) storage

## Right to Erasure (GDPR / CCPA)
Upon receiving a verified deletion request:
1. Purge PII records from active database stores within 30 days.
2. Remove associated document chunks from vector index databases (Qdrant).
3. Log deletion audit event with anonymized request hash.
    `.trim(),
  },
];

export const ALL_PRODUCTS = Array.from(
  new Set(KNOWLEDGE_DOCUMENTS.map((doc) => doc.product))
);

export const ALL_SOURCE_TYPES: SourceType[] = [
  "Support Documentation",
  "Engineering Specification",
  "Developer Reference",
  "Operations Runbook",
  "Regulatory Standard",
];

export function searchKnowledgeBase(
  query: string,
  productFilter: string = "",
  sourceTypeFilter: string = ""
): KnowledgeDocument[] {
  const q = query.trim().toLowerCase();

  return KNOWLEDGE_DOCUMENTS.filter((doc) => {
    const matchesProduct = !productFilter || doc.product === productFilter;
    const matchesType = !sourceTypeFilter || doc.sourceType === sourceTypeFilter;

    if (!matchesProduct || !matchesType) return false;
    if (!q) return true;

    return (
      doc.title.toLowerCase().includes(q) ||
      doc.id.toLowerCase().includes(q) ||
      doc.slug.toLowerCase().includes(q) ||
      doc.summary.toLowerCase().includes(q) ||
      doc.product.toLowerCase().includes(q) ||
      doc.sourceType.toLowerCase().includes(q) ||
      doc.department.toLowerCase().includes(q) ||
      doc.tags.some((tag) => tag.toLowerCase().includes(q))
    );
  });
}

export function getKnowledgeDocumentById(
  idOrSlug: string
): KnowledgeDocument | undefined {
  return KNOWLEDGE_DOCUMENTS.find(
    (doc) => doc.id.toLowerCase() === idOrSlug.toLowerCase() || doc.slug.toLowerCase() === idOrSlug.toLowerCase()
  );
}

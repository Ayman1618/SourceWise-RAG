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

## Summary
This guide outlines the authentication architecture, supported credential mechanisms, session management protocols, and integration standards for the SourceWise Platform. It serves as the authoritative reference for engineers integrating services, configuring identity providers, and securing API access.

---

## 1. Authentication Architecture Overview

The SourceWise Platform implements a zero-trust identity layer centered around OpenID Connect (OIDC) and OAuth 2.0 specifications. All incoming requests to internal and external APIs must present valid, cryptographically signed credentials verified by the Identity Gateway.

```text
[Client / User] ──(OIDC/OAuth 2.0)──> [Identity Gateway] ──(Signed JWT)──> [Internal Microservices]
```

### Core Tenets
* **Stateless Tokens**: Upstream services consume signed JSON Web Tokens (JWT) containing cryptographically verified claims.
* **Least Privilege**: Token scopes are strictly bound to role-based access control (RBAC) definitions.
* **Cryptographic Signing**: Tokens are signed using asymmetric RS256 keys rotated every 90 days.
* **Strict Expiration**: Short-lived access tokens prevent prolonged window of vulnerability.

---

## 2. Supported Authentication Mechanisms

The platform supports three primary authentication methods depending on the client category:

### 2.1 User Interactive Sessions (OIDC & PKCE)
For web and desktop client interactions, SourceWise utilizes the OAuth 2.0 Authorization Code Flow paired with Proof Key for Code Exchange (PKCE) (RFC 7636).
* **Authorization Endpoint**: `https://auth.internal.sourcewise.local/oauth/authorize`
* **Token Endpoint**: `https://auth.internal.sourcewise.local/oauth/token`
* **Token Expiration**:
  * Access Tokens: 15 minutes (900 seconds)
  * Refresh Tokens: 7 days, enforced with absolute rotation on each exchange
* **Supported Scopes**: `openid`, `profile`, `email`, `rag:query`, `rag:ingest`

### 2.2 Service-to-Service Authentication (mTLS & Client Credentials)
Machine-to-machine communications between internal services require OAuth 2.0 Client Credentials or mutual TLS (mTLS).
* Service accounts authenticate via HMAC-SHA256 client credentials or X.509 certificates issued by the Internal Root CA.
* Access tokens for machine accounts are valid for 60 minutes.

### 2.3 API Keys (Developer & Ingestion Access)
For programmatic batch ingestion and local automation scripts, the platform supports API Keys.
* **Header Format**: `X-API-Key: swk_live_<32-character-hex-string>`
* **Storage Standard**: Raw API keys are never stored in plaintext. They are hashed using SHA-256 with a salt before persistence in the credential store.
* **Revocation**: API keys can be instantaneously revoked via the Developer Portal or Admin CLI.

---

## 3. Multi-Factor Authentication (MFA) Requirements

Multi-Factor Authentication is mandatory for all administrative roles and optional but strongly recommended for standard operators.

### 3.1 Supported MFA Factors
1. **Time-Based One-Time Password (TOTP)**: Compatible with RFC 6238 authenticator apps (e.g., Google Authenticator, FreeOTP).
2. **FIDO2 / WebAuthn**: Hardware security keys (e.g., YubiKey 5 Series).
3. **SMS Verification**: Disallowed for internal privileged operations; available only as legacy fallback for external portal users.

### 3.2 MFA Enforcement Policy
* Step-up authentication is automatically triggered when an active session attempts high-risk operations (e.g., vector database purge, role reassignment, or bulk export).
* Users are granted a grace period of 3 attempts before a 15-minute challenge lockout is enforced.

---

## 4. Single Sign-On (SSO) and Directory Integration

Enterprise tenants connect to SourceWise via SAML 2.0 or OIDC federation.

### 4.1 SAML 2.0 Identity Provider (IdP) Setup
* **Entity ID**: `https://auth.internal.sourcewise.local/saml/metadata`
* **Assertion Consumer Service (ACS) URL**: `https://auth.internal.sourcewise.local/saml/consume`
* **Attribute Mapping Requirements**:
  * `urn:oid:0.9.2342.19200300.100.1.1` → `username`
  * `urn:oid:0.9.2342.19200300.100.1.3` → `email`
  * `urn:oid:2.5.4.42` → `givenName`
  * `urn:oid:2.5.4.4` → `surname`
  * `urn:oid:1.3.6.1.4.1.5923.1.5.1.1` → `groups`

### 4.2 Automated Provisioning (SCIM 2.0)
User lifecycle events (creation, profile updates, deactivation) synchronize automatically using the SCIM 2.0 connector at `/scim/v2/Users`. Deactivated users have active tokens revoked within 30 seconds.

---

## 5. Token Lifecycle and Session Management

### 5.1 JSON Web Token Structure
The access token payload conforms to the following schema:
```json
{
  "iss": "https://auth.internal.sourcewise.local",
  "sub": "usr_948194a7e",
  "aud": "sourcewise-rag-api",
  "exp": 1789472400,
  "nbf": 1789471500,
  "iat": 1789471500,
  "jti": "jwt_b28e45f91",
  "department": "Engineering",
  "access_level": "internal",
  "roles": ["rag_operator", "knowledge_contributor"]
}
```

### 5.2 Session Revocation
Sessions can be invalidated through two mechanisms:
1. **Targeted Revocation**: A POST request to `/oauth/revoke` specifying token string and hint type.
2. **Global User Invalidation**: Setting the user's `token_not_before` timestamp to `current_time` in Redis, invalidating all pre-existing JWTs across the fleet.

---

## 6. Technical Troubleshooting

Common authentication errors, root causes, and corrective actions:

| Error Code | HTTP Status | Root Cause | Resolution |
| :--- | :--- | :--- | :--- |
| `AUTH_INVALID_TOKEN` | 401 Unauthorized | JWT expired, malformed signature, or unsupported signing algorithm. | Refresh token or re-authenticate via OAuth authorization flow. Verify clock sync. |
| `AUTH_INSUFFICIENT_SCOPE` | 403 Forbidden | User role lacks requested resource capability (e.g., attempting `rag:ingest` with `rag:query` scope). | Request elevated role assignment from organization administrator. |
| `AUTH_KEY_NOT_FOUND` | 401 Unauthorized | Provided `X-API-Key` has been revoked, expired, or mistyped. | Generate a replacement API key from the Developer Console. |
| `AUTH_MFA_EXPIRED` | 403 Forbidden | Second factor was not completed within the 180-second challenge window. | Re-initiate login flow and input TOTP code immediately. |
| `AUTH_SSO_MISCONFIGURED` | 502 Bad Gateway | Identity Provider returned an unparseable SAML response or expired signing certificate. | Verify IdP certificate validity and ACS URL endpoint binding. |

---

## 7. Related Information

* [Support Login Troubleshooting Guide](./support-login-troubleshooting.md) (`sample-login-troubleshooting`)
* [API Rate Limits and Quota Management](./api-rate-limits.md) (`sample-api-rate-limits`)
* [Document Ingestion Contract](../../docs/document-ingestion-contract.md)

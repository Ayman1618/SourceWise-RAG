---
document_id: sample-login-troubleshooting
title: Support Login Troubleshooting Guide
source_type: troubleshooting_guide
product: SourceWise Platform
version: "1.1"
department: Customer Support
owner: Support Operations
last_updated: "2026-09-16"
access_level: internal
language: en
---

# Support Login Troubleshooting Guide

## Summary
This standard operating procedure (SOP) outlines technical diagnostics, step-by-step resolution workflows, and escalation criteria for customer support engineers addressing user login failures, account lockouts, and identity synchronization issues on the SourceWise Platform.

---

## 1. Triage Quick Reference

Before beginning deep diagnostics, collect the following initial details from the reporting user:
* **User Identifier**: Work email address (`username@example.com`) or system UUID (`usr_*`).
* **Client Environment**: Web browser and version, Operating System, or API client.
* **Timestamp**: Exact time of error occurrence (including timezone) to cross-reference with gateway logs.
* **Exact Error String / Code**: Modal error message, banner text, or HTTP response code.

---

## 2. Common Login Failure Modes

### 2.1 Account Lockout (Exceeded Password Attempts)
* **Trigger**: 5 consecutive incorrect password submissions within a 10-minute window.
* **System Behavior**: Account status transitions to `LOCKED_TEMPORARY` for 30 minutes. Automated password reset emails are suppressed during active lockout to thwart credential stuffing attacks.
* **Support Action**: Support Tier 2 can initiate an administrative reset from the Support Admin Console (`/admin/users/{id}/unlock`) after verifying the user's secondary verification phone or manager approval.

### 2.2 Time Desynchronization / TOTP Clock Drift
* **Trigger**: The client device running the authenticator application (Google Authenticator, Microsoft Authenticator) has a system clock drifting more than 90 seconds from UTC.
* **System Behavior**: Ingestion of the 6-digit TOTP code returns `ERR_MFA_INVALID_PASSCODE` despite user entering the visible digits.
* **Resolution**:
  1. Instruct the user to verify their phone settings: **Settings → System → Date & Time → Set Automatically**.
  2. For Android devices, open Google Authenticator **Settings → Time correction for codes → Sync now**.
  3. If still unsuccessful, execute the MFA Emergency Reset Procedure (Section 4).

### 2.3 SAML / SSO Redirection Loops
* **Trigger**: Expired IdP signing certificates, clock skew between SourceWise and customer Okta/Entra ID, or mismatched entity IDs.
* **Symptom**: User is redirected repeatedly between SourceWise login and customer IdP login without completing session creation.
* **Log Signature**: `SSO_ASSERTION_EXPIRED` or `SAML_RECIPIENT_MISMATCH` in Identity Gateway audit logs.
* **Resolution**: Confirm the customer IdP ACS URL matches `https://auth.internal.sourcewise.local/saml/consume` exactly. Verify customer IdP x509 cert has not lapsed.

---

## 3. Step-by-Step Diagnostic Workflow

```text
[Report Received] 
        │
        ▼
[Check User Status in Admin Console]
   ├── If Status = LOCKED ─────────────> Follow Section 2.1 (Admin Unlock)
   ├── If Status = SUSPENDED ──────────> Escalate to Security Ops
   └── If Status = ACTIVE ─────────────> Inspect Identity Gateway Audit Logs
                                               │
                                               ├── Check MFA Errors ────> Section 4
                                               └── Check SSO Skew ──────> Section 2.3
```

### Step 1: Query User State
Run the internal administrative CLI or query the Support Admin Console:
```bash
sw-admin-cli user get --email "employee@example.com" --fields id,status,mfa_enabled,sso_tenant_id,lockout_expires_at
```

### Step 2: Correlate Gateway Audit Logs
Search the centralized log aggregator (Elastic/Kibana or CloudWatch) for recent events:
```text
service:identity-gateway AND user_id:"usr_948194a7e" AND event_type:"LOGIN_FAILURE"
```

### Step 3: Evaluate Network & Browser Factors
* Ensure browser has third-party cookies enabled if embedded in an iframe or partner portal.
* Clear cached session storage:
  * Chrome/Edge: **Developer Tools (F12) → Application Tab → Storage → Clear Site Data**.
* Disable intrusive browser extensions (ad blockers, privacy filters) that block WebSocket or OAuth redirect params.

---

## 4. MFA Emergency Bypass and Reset Protocol

If a user loses access to their primary multi-factor authenticator device and has exhausted recovery codes:

1. **Identity Verification**: Initiate an out-of-band video call or require written confirmation from the user's direct department manager.
2. **Generate One-Time Bypass Code**:
   * Access Support Admin Console → Security Tools → MFA Reset.
   * Enter Ticket Number, Manager Approval Reference, and Target User ID.
   * Generate an 8-character single-use emergency bypass code (valid for 10 minutes).
3. **Session Re-enrollment**:
   * The user logs in using standard credentials plus the emergency bypass code.
   * The system immediately forces the user to scan a new TOTP QR code and download new recovery codes.

---

## 5. Error Code Reference

| Error Code | User Message | Severity | Handling Tier |
| :--- | :--- | :--- | :--- |
| `ERR_ACCOUNT_LOCKED` | "Account temporarily locked due to excessive failed attempts." | Low | Tier 1 / Tier 2 |
| `ERR_MFA_INVALID_PASSCODE` | "Invalid security code. Please check your time settings and try again." | Low | Tier 1 |
| `ERR_SSO_STATE_MISMATCH` | "Single sign-on validation failed. Contact your organization administrator." | Medium | Tier 2 / Platform Eng |
| `ERR_SESSION_TIMEOUT` | "Your previous session has expired. Please sign in again." | Low | Tier 1 |
| `ERR_IDP_CERT_EXPIRED` | "Unable to verify identity provider signature." | High | Platform Eng / SecOps |

---

## 6. Escalation Matrix

* **Tier 1 (Customer Support)**: Handles password resets, clear-cache advice, browser troubleshooting, and lockout timers.
* **Tier 2 (Senior Support Engineers)**: Handles MFA emergency bypass generation, account un-suspension, audit log parsing.
* **Tier 3 (Platform Engineering)**: Handles systemic SAML certificate rollovers, IdP gateway outages, and database session synchronization failures.
* **Security Operations (SecOps)**: Immediately notified if brute force patterns are detected across more than 10 accounts within an IP subnet.

---

## 7. Related Information

* [Product Authentication Guide](./product-authentication-guide.md) (`sample-authentication-guide`)
* [API Rate Limits and Quota Management](./api-rate-limits.md) (`sample-api-rate-limits`)
* [Document Ingestion Contract](../../docs/document-ingestion-contract.md)

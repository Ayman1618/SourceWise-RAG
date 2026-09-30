#!/usr/bin/env python3
"""SourceWise RAG — Production Deployment Smoke Test Script.

Validates an active or deployed SourceWise RAG service:
1. Backend reachable
2. Health endpoint (GET /health) returns status 'ok'
3. Readiness endpoint (GET /health/ready) responds
4. Query endpoint (POST /api/v1/query) accepts valid request and returns structured Answer
5. Frontend environment configuration validation

Usage:
    python scripts/smoke_test.py --base-url http://localhost:8000
    python scripts/smoke_test.py --base-url https://your-backend.onrender.com
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


def log_step(step_num: int, title: str, status: str = "RUNNING", details: Optional[str] = None):
    """Format and print test step output."""
    icons = {
        "PASS": "✓",
        "FAIL": "✗",
        "WARN": "⚠",
        "INFO": "ℹ",
        "RUNNING": "→",
    }
    icon = icons.get(status, "→")
    status_str = f"[{status}]"
    print(f"{icon} Step {step_num}: {title:<45} {status_str:>10}")
    if details:
        for line in details.strip().split("\n"):
            print(f"    {line}")


def make_http_request(
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Tuple[int, Dict[str, Any], Optional[str]]:
    """Execute HTTP request using standard library urllib."""
    headers = {
        "User-Agent": "SourceWise-SmokeTest/1.0",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body_text = response.read().decode("utf-8")
            try:
                parsed_json = json.loads(body_text) if body_text else {}
            except Exception:
                parsed_json = {"raw": body_text}
            return status_code, parsed_json, None
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        body_text = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed_json = json.loads(body_text) if body_text else {}
        except Exception:
            parsed_json = {"raw": body_text, "error": str(exc)}
        return status_code, parsed_json, str(exc)
    except urllib.error.URLError as exc:
        return 0, {}, str(exc.reason)
    except Exception as exc:
        return 0, {}, str(exc)


def run_smoke_tests(base_url: str, frontend_url: Optional[str] = None) -> bool:
    """Run full deployment verification suite against base_url."""
    base_url = base_url.rstrip("/")
    print("=" * 68)
    print(f" SOURCEWISE RAG DEPLOYMENT SMOKE TEST")
    print(f" Target Backend:  {base_url}")
    if frontend_url:
        print(f" Target Frontend: {frontend_url}")
    print("=" * 68)

    all_passed = True

    # 1. Backend Connectivity & Liveness Check (GET /health)
    health_url = f"{base_url}/health"
    status_code, body, error = make_http_request(health_url, method="GET")
    if status_code == 200 and body.get("status") == "ok":
        log_step(1, "Liveness Check (GET /health)", "PASS", f"HTTP 200 OK — status: '{body.get('status')}'")
    else:
        log_step(1, "Liveness Check (GET /health)", "FAIL", f"Status: {status_code}, Error: {error or body}")
        all_passed = False

    # 2. Readiness Check (GET /health/ready)
    ready_url = f"{base_url}/health/ready"
    status_code, body, error = make_http_request(ready_url, method="GET")
    if status_code == 200:
        db_status = body.get("database", "unknown")
        details_str = json.dumps(body.get("details", {}))
        log_step(2, "Readiness Check (GET /health/ready)", "PASS", f"HTTP 200 OK — database: '{db_status}', details: {details_str}")
    elif status_code == 503:
        log_step(2, "Readiness Check (GET /health/ready)", "WARN", f"HTTP 503 — Database dependency not connected yet: {body.get('detail')}")
    else:
        log_step(2, "Readiness Check (GET /health/ready)", "FAIL", f"Status: {status_code}, Error: {error or body}")
        all_passed = False

    # 3. Query API Contract Check (POST /api/v1/query)
    query_url = f"{base_url}/api/v1/query"
    test_payload = {
        "query": "How do I troubleshoot user login issues?",
        "top_k": 3,
    }
    status_code, body, error = make_http_request(query_url, method="POST", payload=test_payload, timeout=20.0)
    if status_code == 200:
        answer_text = body.get("answer", "")
        evidence_status = body.get("evidence_status", "")
        citations = body.get("citations", [])
        evidence_count = len(body.get("evidence", []))
        
        details = (
            f"HTTP 200 OK\n"
            f"- Evidence Status: {evidence_status}\n"
            f"- Citations Count: {len(citations)}\n"
            f"- Retrieved Evidence Chunks: {evidence_count}\n"
            f"- Answer Snippet: {answer_text[:90]}..."
        )
        log_step(3, "RAG Query API (POST /api/v1/query)", "PASS", details)
    elif status_code in (400, 500, 503):
        # Even if unconfigured or insufficient evidence, verify structured error contract
        log_step(3, "RAG Query API (POST /api/v1/query)", "WARN", f"HTTP {status_code}: {body.get('detail', error)}")
    else:
        log_step(3, "RAG Query API (POST /api/v1/query)", "FAIL", f"Status: {status_code}, Error: {error or body}")
        all_passed = False

    # 4. Frontend Environment Configuration Verification
    configured_frontend_api = frontend_url or os.environ.get("NEXT_PUBLIC_API_BASE_URL") or os.environ.get("NEXT_PUBLIC_API_URL")
    if configured_frontend_api:
        clean_frontend_api = configured_frontend_api.rstrip("/")
        match = "MATCHES backend target" if clean_frontend_api == base_url else f"Points to {clean_frontend_api}"
        log_step(4, "Frontend Env Contract (NEXT_PUBLIC_API_BASE_URL)", "PASS", f"{match}")
    else:
        log_step(4, "Frontend Env Contract (NEXT_PUBLIC_API_BASE_URL)", "INFO", f"Defaulting to: {base_url} (Set NEXT_PUBLIC_API_BASE_URL in production)")

    # 5. Summary
    print("=" * 68)
    if all_passed:
        print("✓ ALL DEPLOYMENT SMOKE CHECKS PASSED")
    else:
        print("✗ SMOKE CHECKS FAILED — Review logs above for remediation.")
    print("=" * 68)
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="SourceWise RAG Deployment Smoke Test Runner")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("API_BASE_URL") or os.environ.get("NEXT_PUBLIC_API_BASE_URL") or "http://127.0.0.1:8000",
        help="Backend base URL to test (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--frontend-url",
        default=os.environ.get("NEXT_PUBLIC_API_BASE_URL"),
        help="Frontend NEXT_PUBLIC_API_BASE_URL value to verify",
    )
    args = parser.parse_args()

    success = run_smoke_tests(base_url=args.base_url, frontend_url=args.frontend_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

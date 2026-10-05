#!/usr/bin/env python3
"""Automated secret-safety scanner for SourceWise RAG.

Scans the repository for sensitive files, leaked credentials, API keys, private keys,
and hardcoded tokens without requiring external services or dependencies.
Designed to run in CI pipelines and pre-commit checks.

Exit codes:
  0: Clean — no secret patterns or untracked sensitive files found.
  1: Violation — one or more potential secrets or sensitive files detected.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

# High-confidence credential patterns
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "Google Gemini API Key": re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b"),
    "OpenAI API Key": re.compile(r"\bsk-[a-zA-Z0-9_-]{24,}\b"),
    "AWS Access Key ID": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub Token": re.compile(r"\b(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b"),
    "Slack Webhook URL": re.compile(r"https://hooks\.slack\.com/services/T[0-9A-Z]+/B[0-9A-Z]+/[0-9A-Za-z]+"),
    "Private Key Block": re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP|PRIVATE) KEY-----"),
    "Database URI with Password": re.compile(
        r"(?:postgres|postgresql|mysql|mongodb|redis)://[a-zA-Z0-9_.-]+:[^@\s/]+@[a-zA-Z0-9_.-]+"
    ),
}

# Patterns for sensitive file names that must NEVER be tracked or committed
FORBIDDEN_FILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\.env(?:\.(?!example$)[^/]+)?$"),  # Matches .env, .env.local, .env.production, etc., but allows .env.example
    re.compile(r".*\.(?:pem|key|p12|pfx|pkcs12)$"),
    re.compile(r".*service[-_]account.*\.json$"),
    re.compile(r"^credentials\.json$"),
    re.compile(r"^id_(?:rsa|ed25519|ecdsa)$"),
]

# Explicit safe test files / allowed dummy patterns for unit testing sanitization logic
KNOWN_TEST_ALLOWLIST: dict[str, set[str]] = {
    "backend/tests/test_indexing.py": {"AIza" + "SyFakeTestTokenForSanitization12345"},
    "backend/tests/test_production_readiness.py": {"postgres" + "://user:SECRET_PASS@host"},
}


def mask_secret(value: str) -> str:
    """Safely mask secret strings to prevent leaking values into console logs."""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def scan_file_content(file_path: Path, relative_path_str: str) -> list[dict[str, str]]:
    """Scan the content of a single file for secret patterns."""
    findings: list[dict[str, str]] = []

    # Exclude scanner definition itself from content checks
    if relative_path_str == "scripts/security_check.py":
        return findings

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return [{"stage": "read", "error": f"Failed to read file: {exc}"}]

    allowed_for_file = KNOWN_TEST_ALLOWLIST.get(relative_path_str, set())

    for pattern_name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(content):
            matched_value = match.group(0)
            if matched_value in allowed_for_file:
                continue

            line_number = content[: match.start()].count("\n") + 1
            findings.append(
                {
                    "file": relative_path_str,
                    "line": str(line_number),
                    "rule": pattern_name,
                    "preview": mask_secret(matched_value),
                }
            )

    return findings


def get_tracked_files(repo_root: Path) -> list[str]:
    """Retrieve list of files tracked by git."""
    try:
        output = subprocess.check_output(
            ["git", "ls-files"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
        ).decode("utf-8")
        return [f.strip() for f in output.splitlines() if f.strip()]
    except Exception:
        # Fallback to traversing files on disk excluding build artifacts
        files: list[str] = []
        for p in repo_root.rglob("*"):
            if p.is_file():
                rel = p.relative_to(repo_root).as_posix()
                if not any(part in rel.split("/") for part in [".git", "node_modules", ".venv", "__pycache__", ".next"]):
                    files.append(rel)
        return files


def run_security_check(repo_root: Path, verbose: bool = False) -> tuple[bool, list[str]]:
    """Execute complete repository secret scan."""
    tracked_files = get_tracked_files(repo_root)
    violations: list[str] = []

    # 1. Check for forbidden filenames in tracked repository
    for file_rel in tracked_files:
        filename = Path(file_rel).name
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if pattern.search(filename) or pattern.search(file_rel):
                violations.append(
                    f"FORBIDDEN FILE: Tracked sensitive file matched forbidden pattern: {file_rel}"
                )

    # 2. Check content of tracked files
    for file_rel in tracked_files:
        # Skip binary files or lock files
        if file_rel.endswith((".png", ".jpg", ".jpeg", ".ico", ".pdf", ".lock")):
            continue

        full_path = repo_root / file_rel
        if not full_path.is_file():
            continue

        findings = scan_file_content(full_path, file_rel)
        for finding in findings:
            if "error" in finding:
                violations.append(f"ERROR: {file_rel} — {finding['error']}")
            else:
                violations.append(
                    f"CREDENTIAL MATCH: {finding['file']}:{finding['line']} "
                    f"[{finding['rule']}] (masked: {finding['preview']})"
                )

    is_clean = len(violations) == 0
    return is_clean, violations


def main() -> None:
    """CLI entrypoint for repository secret scanner."""
    parser = argparse.ArgumentParser(
        description="SourceWise automated secret and credential safety scanner."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Path to repository root (defaults to automatic detection).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose progress messages.",
    )

    args = parser.parse_args()

    repo_root = (
        Path(args.root).resolve()
        if args.root
        else Path(__file__).resolve().parent.parent
    )

    print(f"Running SourceWise Secret Scanner on: {repo_root}")
    is_clean, violations = run_security_check(repo_root, verbose=args.verbose)

    if is_clean:
        print("✓ Secret Safety Check: PASSED (0 credentials or forbidden files detected)")
        sys.exit(0)
    else:
        print(f"✗ Secret Safety Check: FAILED ({len(violations)} violation(s) detected):")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)


if __name__ == "__main__":
    main()

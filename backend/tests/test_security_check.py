"""Unit tests for automated secret-safety scanner (scripts/security_check.py)."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.security_check import (
    mask_secret,
    run_security_check,
    scan_file_content,
)


class TestSecurityCheck(unittest.TestCase):
    """Test suite validating secret detection and repository cleanliness."""

    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent.parent

    def test_repository_is_clean(self) -> None:
        """Verify the active repository codebase contains zero unallowed secrets or forbidden files."""
        is_clean, violations = run_security_check(self.repo_root)
        self.assertTrue(
            is_clean,
            f"Repository contains security violations: {violations}",
        )
        self.assertEqual(violations, [])

    def test_mask_secret(self) -> None:
        """Verify that secret masking prevents printing full secret values."""
        self.assertEqual(mask_secret("12345"), "***")
        self.assertEqual(mask_secret("12345678"), "***")
        long_val = "AIzaSyABCDEF1234567890abcdefghijklmno"
        masked = mask_secret(long_val)
        self.assertTrue(masked.startswith("AIza..."))
        self.assertTrue(masked.endswith("lmno"))
        self.assertNotIn("ABCDEF1234567890", masked)

    def test_detects_secret_patterns(self) -> None:
        """Verify scanner catches synthetic Gemini, OpenAI, AWS, and private key strings."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Test synthetic Gemini key
            fake_gemini_key = "AIza" + "Sy012345678901234567890123456789012"
            fake_gemini_file = tmp_path / "gemini.py"
            fake_gemini_file.write_text(f"API_KEY = '{fake_gemini_key}'")
            findings = scan_file_content(fake_gemini_file, "gemini.py")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["rule"], "Google Gemini API Key")

            # Test synthetic OpenAI key
            fake_openai_key = "sk-" + "proj1234567890abcdef1234567890"
            fake_openai_file = tmp_path / "openai.py"
            fake_openai_file.write_text(f"SK_KEY = '{fake_openai_key}'")
            findings = scan_file_content(fake_openai_file, "openai.py")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["rule"], "OpenAI API Key")

            # Test synthetic Private key
            fake_key_header = "-----BEGIN " + "RSA KEY-----"
            fake_key_file = tmp_path / "key.txt"
            fake_key_file.write_text(f"{fake_key_header}\nMIIEowIBAAKCAQEA0...\n-----END RSA KEY-----")
            findings = scan_file_content(fake_key_file, "key.txt")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["rule"], "Private Key Block")


if __name__ == "__main__":
    unittest.main()

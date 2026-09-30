"""Tests for deployment smoke test script."""

import json
from unittest.mock import MagicMock, patch
import pytest

from scripts.smoke_test import make_http_request, run_smoke_tests


class TestSmokeTestScript:
    """Validate smoke test execution logic and error handling."""

    @patch("urllib.request.urlopen")
    def test_make_http_request_success_json(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps({"status": "ok"}).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        status, body, error = make_http_request("http://localhost:8000/health")
        assert status == 200
        assert body == {"status": "ok"}
        assert error is None

    @patch("scripts.smoke_test.make_http_request")
    def test_run_smoke_tests_all_pass(self, mock_make_request):
        # 1. /health -> 200
        # 2. /health/ready -> 200
        # 3. /api/v1/query -> 200
        mock_make_request.side_effect = [
            (200, {"status": "ok"}, None),
            (200, {"status": "ready", "database": "connected", "details": {"collection_exists": True}}, None),
            (200, {
                "answer": "This is a verified grounded answer.",
                "evidence_status": "sufficient",
                "citations": [{"citation_id": "cite_1"}],
                "evidence": [{"chunk": {"chunk_id": "doc#1"}}]
            }, None),
        ]

        result = run_smoke_tests(base_url="http://localhost:8000", frontend_url="http://localhost:8000")
        assert result is True

    @patch("scripts.smoke_test.make_http_request")
    def test_run_smoke_tests_health_fail(self, mock_make_request):
        mock_make_request.side_effect = [
            (500, {"error": "Internal Error"}, "Server error"),
            (200, {"status": "ready"}, None),
            (200, {"answer": "Answer"}, None),
        ]

        result = run_smoke_tests(base_url="http://localhost:8000")
        assert result is False

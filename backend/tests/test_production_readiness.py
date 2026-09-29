"""Unit and integration tests for production configuration, CORS, health, and readiness endpoints."""

import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.api.deps import get_vector_store_service
from app.core.config import Settings
from app.main import create_app
from app.services.vector_store import BaseVectorStoreService


class TestProductionConfiguration(unittest.TestCase):
    """Test suite for environment-driven production configuration and CORS parsing."""

    def test_default_development_configuration(self) -> None:
        """Verify standard defaults for local development."""
        s = Settings()
        self.assertEqual(s.backend_host, "0.0.0.0")
        self.assertEqual(s.backend_port, 8000)
        self.assertEqual(s.effective_port, 8000)
        self.assertIn("http://localhost:3000", s.allowed_cors_origins)

    def test_dynamic_port_resolution_override(self) -> None:
        """Verify cloud platform PORT environment variable overrides default port."""
        s = Settings(port=10000, backend_port=8000)
        self.assertEqual(s.effective_port, 10000)

        s_no_port = Settings(port=None, backend_port=9000)
        self.assertEqual(s_no_port.effective_port, 9000)

    def test_cors_origins_parsing_comma_separated(self) -> None:
        """Verify comma-separated string parsing for CORS origins."""
        s = Settings(cors_origins="https://app.sourcewise.io, https://sourcewise.vercel.app/")
        origins = s.allowed_cors_origins
        self.assertEqual(len(origins), 2)
        self.assertIn("https://app.sourcewise.io", origins)
        self.assertIn("https://sourcewise.vercel.app", origins)

    def test_cors_origins_parsing_json_array(self) -> None:
        """Verify JSON-formatted array parsing for CORS origins."""
        s = Settings(cors_origins='["https://frontend.com", "http://localhost:3000"]')
        origins = s.allowed_cors_origins
        self.assertEqual(origins, ["https://frontend.com", "http://localhost:3000"])

    def test_cors_origins_list_format(self) -> None:
        """Verify list parsing and trailing slash stripping."""
        s = Settings(cors_origins=["https://demo.example.com/", "http://127.0.0.1:3000"])
        self.assertEqual(s.allowed_cors_origins, ["https://demo.example.com", "http://127.0.0.1:3000"])


class TestHealthAndReadinessEndpoints(unittest.TestCase):
    """Test suite for liveness (/health) and readiness (/health/ready) endpoints."""

    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_liveness_health_endpoint_success(self) -> None:
        """Verify /health returns 200 OK without any external dependency checks."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data, {"status": "ok"})

    def test_readiness_endpoint_success(self) -> None:
        """Verify /health/ready returns 200 OK when vector store dependency is connected."""
        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.collection_exists.return_value = True

        self.app.dependency_overrides[get_vector_store_service] = lambda: mock_vector_store

        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["database"], "connected")
        self.assertTrue(data["details"]["collection_exists"])

        self.app.dependency_overrides.clear()

    def test_readiness_endpoint_failure_when_database_unreachable(self) -> None:
        """Verify /health/ready returns 503 Service Unavailable when vector store fails."""
        mock_vector_store = MagicMock(spec=BaseVectorStoreService)
        mock_vector_store.collection_exists.side_effect = ConnectionError("Qdrant cluster connection refused")

        self.app.dependency_overrides[get_vector_store_service] = lambda: mock_vector_store

        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Vector database dependency is currently unreachable", data["detail"])

        self.app.dependency_overrides.clear()


class TestCORSIntegration(unittest.TestCase):
    """Test suite verifying CORS middleware behavior with configured origins."""

    def test_cors_allowed_origin(self) -> None:
        """Verify CORS headers are returned for configured frontend origin."""
        with patch.object(Settings, "allowed_cors_origins", ["https://sourcewise.vercel.app"]):
            app = create_app()
            client = TestClient(app)

            headers = {
                "Origin": "https://sourcewise.vercel.app",
                "Access-Control-Request-Method": "POST",
            }
            response = client.options("/api/v1/query", headers=headers)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.headers.get("access-control-allow-origin"),
                "https://sourcewise.vercel.app",
            )

    def test_cors_disallowed_origin(self) -> None:
        """Verify CORS headers omit unauthorized origins in production-configured mode."""
        with patch.object(Settings, "allowed_cors_origins", ["https://trusted-frontend.com"]):
            app = create_app()
            client = TestClient(app)

            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
            }
            response = client.options("/api/v1/query", headers=headers)
            # Middleware should not grant access to disallowed origin
            self.assertNotEqual(
                response.headers.get("access-control-allow-origin"),
                "https://malicious-site.com",
            )


if __name__ == "__main__":
    unittest.main()

"""Unit tests for embedding service interface and Google Gemini implementation."""

import unittest
from unittest.mock import MagicMock

from google.genai import types

from app.core.config import settings
from app.services.embedding import (
    BaseEmbeddingService,
    GeminiEmbeddingService,
    OpenAIEmbeddingService,
)


class TestEmbeddingService(unittest.TestCase):
    """Test suite for embedding service contracts and Gemini embedding implementation."""

    def test_base_embedding_service_cannot_be_instantiated(self) -> None:
        """Verify abstract base class enforces method implementation."""
        with self.assertRaises(TypeError):
            BaseEmbeddingService()  # type: ignore[abstract]

    def test_concrete_mock_subclass(self) -> None:
        """Verify BaseEmbeddingService can be subclassed cleanly."""

        class MockEmbeddingService(BaseEmbeddingService):
            def embed_text(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3]

            def embed_texts(self, texts: list[str]) -> list[list[float]]:
                return [[0.1, 0.2, 0.3] for _ in texts]

            def query_embedding(self, query: str) -> list[float]:
                return [0.1, 0.2, 0.3]

        service = MockEmbeddingService()
        self.assertIsInstance(service, BaseEmbeddingService)
        self.assertEqual(service.embed_text("test"), [0.1, 0.2, 0.3])
        self.assertEqual(service.embed_texts(["a", "b"]), [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]])
        self.assertEqual(service.query_embedding("search"), [0.1, 0.2, 0.3])

    def test_gemini_configuration_defaults(self) -> None:
        """Verify settings default to Gemini free-tier models and configurations."""
        from app.core.config import Settings

        test_settings = Settings()
        self.assertEqual(test_settings.gemini_generation_model, "gemini-2.5-flash-lite")
        self.assertEqual(test_settings.gemini_embedding_model, "gemini-embedding-2")
        self.assertEqual(test_settings.gemini_embedding_dimension, 1536)
        self.assertEqual(test_settings.embedding_provider, "gemini")
        self.assertEqual(test_settings.llm_provider, "gemini")
        self.assertEqual(test_settings.qdrant_vector_size, 1536)

    def test_gemini_embedding_service_defaults(self) -> None:
        """Verify Gemini embedding service initializes with settings defaults."""
        mock_client = MagicMock()
        service = GeminiEmbeddingService(client=mock_client)

        self.assertEqual(service.model, settings.gemini_embedding_model)
        self.assertEqual(service.dimension, settings.gemini_embedding_dimension)
        self.assertEqual(service.batch_size, settings.embedding_batch_size)
        self.assertEqual(service.client, mock_client)


    def test_gemini_embedding_service_custom_config(self) -> None:
        """Verify Gemini embedding service accepts custom configuration overrides."""
        mock_client = MagicMock()
        service = GeminiEmbeddingService(
            api_key="custom-gemini-key",
            model="gemini-embedding-2",
            dimension=768,
            batch_size=32,
            client=mock_client,
        )

        self.assertEqual(service.model, "gemini-embedding-2")
        self.assertEqual(service.dimension, 768)
        self.assertEqual(service.batch_size, 32)
        self.assertEqual(service._api_key, "custom-gemini-key")

    def test_embed_text_success(self) -> None:
        """Verify embed_text correctly invokes Gemini embed_content API and parses vector."""
        mock_client = MagicMock()
        mock_item = MagicMock(values=[0.01, 0.02, 0.03, 0.04])
        mock_client.models.embed_content.return_value = MagicMock(embeddings=[mock_item])

        service = GeminiEmbeddingService(
            client=mock_client,
            model="gemini-embedding-2",
            dimension=1536,
        )
        result = service.embed_text("SourceWise RAG evidence")

        self.assertEqual(result, [0.01, 0.02, 0.03, 0.04])
        mock_client.models.embed_content.assert_called_once()
        _, kwargs = mock_client.models.embed_content.call_args
        self.assertEqual(kwargs["model"], "gemini-embedding-2")
        self.assertEqual(kwargs["contents"], "SourceWise RAG evidence")
        self.assertIsInstance(kwargs["config"], types.EmbedContentConfig)
        self.assertEqual(kwargs["config"].output_dimensionality, 1536)

    def test_embed_text_empty_input_raises_value_error(self) -> None:
        """Verify embed_text raises ValueError on blank/empty text."""
        mock_client = MagicMock()
        service = GeminiEmbeddingService(client=mock_client)

        with self.assertRaises(ValueError) as ctx:
            service.embed_text("")
        self.assertIn("empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            service.embed_text("   \n\t  ")
        self.assertIn("empty", str(ctx.exception))

        mock_client.models.embed_content.assert_not_called()

    def test_embed_text_api_returns_no_embeddings_raises_value_error(self) -> None:
        """Verify embed_text raises ValueError when Gemini returns empty embeddings."""
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = MagicMock(embeddings=[])

        service = GeminiEmbeddingService(client=mock_client)
        with self.assertRaises(ValueError) as ctx:
            service.embed_text("test")
        self.assertIn("No embeddings returned", str(ctx.exception))

    def test_embed_texts_empty_list_returns_empty(self) -> None:
        """Verify embed_texts returns empty list for empty input without calling API."""
        mock_client = MagicMock()
        service = GeminiEmbeddingService(client=mock_client)

        result = service.embed_texts([])
        self.assertEqual(result, [])
        mock_client.models.embed_content.assert_not_called()

    def test_embed_texts_single_batch(self) -> None:
        """Verify embed_texts correctly processes a single batch with ordered results."""
        mock_client = MagicMock()
        item_0 = MagicMock(values=[0.1, 0.1])
        item_1 = MagicMock(values=[0.2, 0.2])
        mock_client.models.embed_content.return_value = MagicMock(embeddings=[item_0, item_1])

        service = GeminiEmbeddingService(client=mock_client, batch_size=10, dimension=1536)
        texts = ["first text", "second text"]
        result = service.embed_texts(texts)

        self.assertEqual(result, [[0.1, 0.1], [0.2, 0.2]])
        mock_client.models.embed_content.assert_called_once()
        _, kwargs = mock_client.models.embed_content.call_args
        self.assertEqual(kwargs["contents"], texts)
        self.assertEqual(kwargs["config"].output_dimensionality, 1536)

    def test_embed_texts_multi_batch(self) -> None:
        """Verify embed_texts splits input across batches according to batch_size."""
        mock_client = MagicMock()

        batch_1_res = [MagicMock(values=[0.1]), MagicMock(values=[0.2])]
        batch_2_res = [MagicMock(values=[0.3]), MagicMock(values=[0.4])]
        batch_3_res = [MagicMock(values=[0.5])]

        mock_client.models.embed_content.side_effect = [
            MagicMock(embeddings=batch_1_res),
            MagicMock(embeddings=batch_2_res),
            MagicMock(embeddings=batch_3_res),
        ]

        service = GeminiEmbeddingService(client=mock_client, batch_size=2)
        texts = ["text1", "text2", "text3", "text4", "text5"]
        result = service.embed_texts(texts)

        self.assertEqual(result, [[0.1], [0.2], [0.3], [0.4], [0.5]])
        self.assertEqual(mock_client.models.embed_content.call_count, 3)

    def test_embed_texts_invalid_item_raises_value_error(self) -> None:
        """Verify embed_texts rejects any blank entry in the list."""
        mock_client = MagicMock()
        service = GeminiEmbeddingService(client=mock_client)

        with self.assertRaises(ValueError) as ctx:
            service.embed_texts(["valid text", "   ", "another valid"])
        self.assertIn("index 1", str(ctx.exception))
        mock_client.models.embed_content.assert_not_called()

    def test_embed_texts_count_mismatch_raises_value_error(self) -> None:
        """Verify embed_texts detects mismatch between requested count and returned embeddings."""
        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = MagicMock(embeddings=[MagicMock(values=[0.1])])

        service = GeminiEmbeddingService(client=mock_client, batch_size=10)
        with self.assertRaises(ValueError) as ctx:
            service.embed_texts(["text1", "text2"])
        self.assertIn("Embedding count mismatch", str(ctx.exception))

    def test_query_embedding_success(self) -> None:
        """Verify query_embedding generates embedding for search queries."""
        mock_client = MagicMock()
        mock_item = MagicMock(values=[0.9, 0.8, 0.7])
        mock_client.models.embed_content.return_value = MagicMock(embeddings=[mock_item])

        service = GeminiEmbeddingService(client=mock_client, dimension=1536)
        result = service.query_embedding("how to configure sourcewise")

        self.assertEqual(result, [0.9, 0.8, 0.7])
        mock_client.models.embed_content.assert_called_once()
        _, kwargs = mock_client.models.embed_content.call_args
        self.assertEqual(kwargs["contents"], "how to configure sourcewise")
        self.assertEqual(kwargs["config"].output_dimensionality, 1536)

    def test_query_embedding_empty_raises_value_error(self) -> None:
        """Verify query_embedding rejects blank queries."""
        mock_client = MagicMock()
        service = GeminiEmbeddingService(client=mock_client)

        with self.assertRaises(ValueError):
            service.query_embedding("   ")

    def test_api_failure_handling(self) -> None:
        """Verify that Gemini API network/quota errors are cleanly propagated."""
        mock_client = MagicMock()
        mock_client.models.embed_content.side_effect = RuntimeError("ResourceExhausted: Free tier quota exceeded")

        service = GeminiEmbeddingService(client=mock_client)
        with self.assertRaises(RuntimeError) as ctx:
            service.embed_text("test")
        self.assertIn("ResourceExhausted", str(ctx.exception))

    def test_openai_embedding_service_backward_compatibility(self) -> None:
        """Verify optional OpenAI embedding service can still be used if client passed."""
        mock_client = MagicMock()
        mock_item = MagicMock(embedding=[0.1, 0.2])
        mock_client.embeddings.create.return_value = MagicMock(data=[mock_item])

        service = OpenAIEmbeddingService(client=mock_client, model="text-embedding-3-small")
        self.assertEqual(service.embed_text("test"), [0.1, 0.2])


if __name__ == "__main__":
    unittest.main()


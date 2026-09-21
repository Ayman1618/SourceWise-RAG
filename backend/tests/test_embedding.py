"""Unit tests for embedding service and OpenAI-compatible implementation."""

import unittest
from unittest.mock import MagicMock

from app.core.config import settings
from app.services.embedding import BaseEmbeddingService, OpenAIEmbeddingService


class TestEmbeddingService(unittest.TestCase):
    """Test suite for embedding service contracts and OpenAI embedding implementation."""

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

    def test_openai_embedding_service_defaults(self) -> None:
        """Verify service initializes with settings defaults."""
        mock_client = MagicMock()
        service = OpenAIEmbeddingService(client=mock_client)

        self.assertEqual(service.model, settings.embedding_model)
        self.assertEqual(service.batch_size, settings.embedding_batch_size)
        self.assertEqual(service.client, mock_client)

    def test_openai_embedding_service_custom_config(self) -> None:
        """Verify service accepts custom configuration overrides."""
        mock_client = MagicMock()
        service = OpenAIEmbeddingService(
            api_key="custom-key",
            model="custom-embedding-model",
            base_url="https://custom-provider.com/v1",
            batch_size=32,
            client=mock_client,
        )

        self.assertEqual(service.model, "custom-embedding-model")
        self.assertEqual(service.batch_size, 32)
        self.assertEqual(service._api_key, "custom-key")
        self.assertEqual(service._base_url, "https://custom-provider.com/v1")

    def test_embed_text_success(self) -> None:
        """Verify embed_text correctly invokes OpenAI embeddings API and parses vector."""
        mock_client = MagicMock()
        mock_item = MagicMock()
        mock_item.embedding = [0.01, 0.02, 0.03, 0.04]
        mock_client.embeddings.create.return_value = MagicMock(data=[mock_item])

        service = OpenAIEmbeddingService(client=mock_client, model="text-embedding-3-small")
        result = service.embed_text("SourceWise RAG evidence")

        self.assertEqual(result, [0.01, 0.02, 0.03, 0.04])
        mock_client.embeddings.create.assert_called_once_with(
            input="SourceWise RAG evidence",
            model="text-embedding-3-small",
        )

    def test_embed_text_empty_input_raises_value_error(self) -> None:
        """Verify embed_text raises ValueError on blank/empty text."""
        mock_client = MagicMock()
        service = OpenAIEmbeddingService(client=mock_client)

        with self.assertRaises(ValueError) as ctx:
            service.embed_text("")
        self.assertIn("empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            service.embed_text("   \n\t  ")
        self.assertIn("empty", str(ctx.exception))

        mock_client.embeddings.create.assert_not_called()

    def test_embed_texts_empty_list_returns_empty(self) -> None:
        """Verify embed_texts returns empty list for empty input without calling API."""
        mock_client = MagicMock()
        service = OpenAIEmbeddingService(client=mock_client)

        result = service.embed_texts([])
        self.assertEqual(result, [])
        mock_client.embeddings.create.assert_not_called()

    def test_embed_texts_single_batch(self) -> None:
        """Verify embed_texts correctly processes a single batch with ordered results."""
        mock_client = MagicMock()

        # Simulate unordered response from API to test index sorting
        item_1 = MagicMock(index=1, embedding=[0.2, 0.2])
        item_0 = MagicMock(index=0, embedding=[0.1, 0.1])
        mock_client.embeddings.create.return_value = MagicMock(data=[item_1, item_0])

        service = OpenAIEmbeddingService(client=mock_client, batch_size=10)
        texts = ["first text", "second text"]
        result = service.embed_texts(texts)

        self.assertEqual(result, [[0.1, 0.1], [0.2, 0.2]])
        mock_client.embeddings.create.assert_called_once_with(
            input=texts,
            model=service.model,
        )

    def test_embed_texts_multi_batch(self) -> None:
        """Verify embed_texts splits input across batches according to batch_size."""
        mock_client = MagicMock()

        batch_1_res = [MagicMock(index=0, embedding=[0.1]), MagicMock(index=1, embedding=[0.2])]
        batch_2_res = [MagicMock(index=0, embedding=[0.3]), MagicMock(index=1, embedding=[0.4])]
        batch_3_res = [MagicMock(index=0, embedding=[0.5])]

        mock_client.embeddings.create.side_effect = [
            MagicMock(data=batch_1_res),
            MagicMock(data=batch_2_res),
            MagicMock(data=batch_3_res),
        ]

        service = OpenAIEmbeddingService(client=mock_client, batch_size=2)
        texts = ["text1", "text2", "text3", "text4", "text5"]
        result = service.embed_texts(texts)

        self.assertEqual(result, [[0.1], [0.2], [0.3], [0.4], [0.5]])
        self.assertEqual(mock_client.embeddings.create.call_count, 3)

    def test_embed_texts_invalid_item_raises_value_error(self) -> None:
        """Verify embed_texts rejects any blank entry in the list."""
        mock_client = MagicMock()
        service = OpenAIEmbeddingService(client=mock_client)

        with self.assertRaises(ValueError) as ctx:
            service.embed_texts(["valid text", "   ", "another valid"])
        self.assertIn("index 1", str(ctx.exception))
        mock_client.embeddings.create.assert_not_called()

    def test_query_embedding_success(self) -> None:
        """Verify query_embedding generates embedding for search queries."""
        mock_client = MagicMock()
        mock_item = MagicMock(embedding=[0.9, 0.8, 0.7])
        mock_client.embeddings.create.return_value = MagicMock(data=[mock_item])

        service = OpenAIEmbeddingService(client=mock_client)
        result = service.query_embedding("how to configure sourcewise")

        self.assertEqual(result, [0.9, 0.8, 0.7])
        mock_client.embeddings.create.assert_called_once_with(
            input="how to configure sourcewise",
            model=service.model,
        )

    def test_query_embedding_empty_raises_value_error(self) -> None:
        """Verify query_embedding rejects blank queries."""
        mock_client = MagicMock()
        service = OpenAIEmbeddingService(client=mock_client)

        with self.assertRaises(ValueError):
            service.query_embedding("   ")


if __name__ == "__main__":
    unittest.main()

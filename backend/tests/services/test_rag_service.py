"""
RAGService tests.

Covers the embed_text method by replacing the module-level Ollama
embeddings object with a lightweight fake — no real Ollama server needed.
"""
import numpy as np
import pytest

from app.services.rag_service import RAGService


# ─────────────────────────────────────────────────────────────────────────────
# RAGService.embed_text
# ─────────────────────────────────────────────────────────────────────────────

def test_embed_text_calls_embed_query_with_the_provided_text(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import rag_service as rag_module

    captured_queries: list[str] = []

    class FakeEmbeddings:
        def embed_query(self, text: str) -> list[float]:
            captured_queries.append(text)
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr(rag_module, "embeddings", FakeEmbeddings())

    # When
    RAGService.embed_text("Pythagorean theorem")

    # Then
    assert captured_queries == ["Pythagorean theorem"]


def test_embed_text_returns_numpy_array_of_float32(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import rag_service as rag_module

    class FakeEmbeddings:
        def embed_query(self, text: str) -> list[float]:
            return [1.0, 2.0, 3.0]

    monkeypatch.setattr(rag_module, "embeddings", FakeEmbeddings())

    # When
    result = RAGService.embed_text("any text")

    # Then
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32


def test_embed_text_preserves_all_embedding_values(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import rag_service as rag_module

    expected = [0.25, 0.5, 0.75, 1.0]

    class FakeEmbeddings:
        def embed_query(self, text: str) -> list[float]:
            return expected

    monkeypatch.setattr(rag_module, "embeddings", FakeEmbeddings())

    # When
    result = RAGService.embed_text("test")

    # Then
    np.testing.assert_array_almost_equal(result, np.array(expected, dtype=np.float32))

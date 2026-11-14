"""Unit tests for Phase 4 retrieval module (FAISS vector store and embedding adapter)."""

import numpy as np
import pytest

from src.baselines.models import Chunk
from src.retrieval.embeddings import ModelTokenizer
from src.retrieval.faiss_store import FAISSVectorStore


class MockHFTokenizer:
    """Mock HuggingFace tokenizer for isolated fast unit testing."""

    def encode(self, text: str, add_special_tokens: bool = False):
        if not text:
            return []
        tokens = [hash(c) % 1000 for c in text.split()]
        return [101] + tokens + [102] if add_special_tokens else tokens

    def tokenize(self, text: str):
        if not text:
            return []
        return text.split()


@pytest.fixture
def sample_chunks():
    return [
        Chunk(
            chunk_id="c0",
            text="First test chunk about attention mechanisms.",
            page_start=1,
            page_end=1,
            token_count=6,
            strategy="test",
        ),
        Chunk(
            chunk_id="c1",
            text="Second test chunk about deep bidirectional transformers.",
            page_start=2,
            page_end=2,
            token_count=7,
            strategy="test",
        ),
        Chunk(
            chunk_id="c2",
            text="Third test chunk about retrieval augmented generation.",
            page_start=3,
            page_end=3,
            token_count=6,
            strategy="test",
        ),
    ]


def test_model_tokenizer_adapter():
    mock_hf = MockHFTokenizer()
    adapter = ModelTokenizer(mock_hf)

    text = "Scaled Dot-Product Attention"
    tokens = adapter.tokenize(text)
    count = adapter.count_tokens(text)

    assert len(tokens) == 3
    assert count == 3
    assert adapter(text) == 3
    assert adapter.count_tokens("") == 0
    assert adapter.tokenize("") == []


def test_faiss_store_initialization():
    store = FAISSVectorStore(dimension=16)
    assert store.dimension == 16
    assert store.total_vectors == 0
    assert len(store) == 0


def test_faiss_store_add_and_search(sample_chunks):
    dim = 4
    store = FAISSVectorStore(dimension=dim)

    # 3 distinct orthogonal-ish vectors normalized to unit length
    embeddings = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ], dtype=np.float32)

    store.add_chunks(sample_chunks, embeddings)
    assert store.total_vectors == 3
    assert len(store) == 3

    # Query matching vector 0 exactly
    query_0 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    hits = store.search(query_0, top_k=2)

    assert len(hits) == 2
    top_chunk, score, rank = hits[0]
    assert rank == 1
    assert top_chunk.chunk_id == "c0"
    assert pytest.approx(score, abs=1e-5) == 1.0

    # Query matching vector 1 exactly
    query_1 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    hits_1 = store.search(query_1, top_k=1)
    assert len(hits_1) == 1
    assert hits_1[0][0].chunk_id == "c1"
    assert pytest.approx(hits_1[0][1], abs=1e-5) == 1.0


def test_faiss_store_empty_search():
    store = FAISSVectorStore(dimension=8)
    query = np.zeros(8, dtype=np.float32)
    hits = store.search(query, top_k=5)
    assert hits == []


def test_faiss_store_reset(sample_chunks):
    store = FAISSVectorStore(dimension=2)
    embeddings = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    store.add_chunks(sample_chunks[:2], embeddings)
    assert store.total_vectors == 2

    store.reset()
    assert store.total_vectors == 0
    assert len(store.chunks) == 0


def test_faiss_store_dimension_mismatch(sample_chunks):
    store = FAISSVectorStore(dimension=4)
    bad_embeddings = np.ones((len(sample_chunks), 8), dtype=np.float32)
    with pytest.raises(ValueError, match="Embedding dimension"):
        store.add_chunks(sample_chunks, bad_embeddings)

    # Valid chunks but bad query dimension
    good_embeddings = np.ones((len(sample_chunks), 4), dtype=np.float32)
    store.add_chunks(sample_chunks, good_embeddings)
    bad_query = np.zeros(8, dtype=np.float32)
    with pytest.raises(ValueError, match="Query dimension"):
        store.search(bad_query, top_k=2)


def test_faiss_store_chunk_count_mismatch(sample_chunks):
    store = FAISSVectorStore(dimension=4)
    embeddings = np.ones((2, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="Chunk count"):
        store.add_chunks(sample_chunks, embeddings)


def test_embedding_manager_inference(monkeypatch):
    from unittest.mock import MagicMock
    from src.retrieval.embeddings import EmbeddingManager

    mock_st = MagicMock()
    mock_st.get_embedding_dimension.return_value = 384
    mock_st.tokenizer = MockHFTokenizer()
    mock_st.encode.return_value = np.ones((1, 384), dtype=np.float32)

    import sentence_transformers
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", lambda *args, **kwargs: mock_st)

    mgr = EmbeddingManager("test-model")
    assert mgr.dimension == 384
    assert mgr.count_tokens("Hello world") == 2
    emb = mgr.encode(["Test embedding sentence"])
    assert emb.shape == (1, 384)


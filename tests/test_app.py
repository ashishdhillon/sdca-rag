"""Unit tests for Phase 5 Streamlit application logic and data integration."""

import numpy as np
import pandas as pd
import pytest

from src.baselines.models import Chunk
from src.extraction.models import Document, Page, TextBlock, TextSpan
from src.retrieval.faiss_store import FAISSVectorStore


def make_synthetic_document() -> Document:
    span = TextSpan(text="Attention is a neural network mechanism.", bbox=(50.0, 50.0, 400.0, 70.0), font="Helvetica", font_size=10.0, flags=0)
    block = TextBlock(block_id=0, bbox=span.bbox, text=span.text, block_type=0, spans=[span])
    page = Page(page_number=1, width=595.0, height=842.0, blocks=[block])
    return Document(source_path="<test-doc>", page_count=1, pages=[page])


def test_benchmark_summary_data_loading():
    from src.app.streamlit_app import load_official_benchmark_summary

    df = load_official_benchmark_summary()
    assert df is not None, "Failed to load official benchmark summary"
    assert len(df) == 4, f"Expected 4 strategies, got {len(df)}"

    expected_cols = [
        "strategy",
        "total_chunks",
        "mean_tokens",
        "median_tokens",
        "min_tokens",
        "max_tokens",
        "std_tokens",
        "mean_precision_at_5",
        "mean_recall_at_5",
        "hit_rate_at_5",
        "mrr",
        "mean_ndcg_at_5",
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"

    strategies = set(df["strategy"].str.lower())
    assert strategies == {"fixed", "recursive", "sentence", "sdca"}


def test_benchmark_detailed_results_loading():
    from src.app.streamlit_app import load_official_retrieval_results

    df = load_official_retrieval_results()
    assert df is not None, "Failed to load official retrieval results"
    assert len(df) == 60, f"Expected 60 query-strategy rows, got {len(df)}"

    required_cols = [
        "query_id",
        "pdf_id",
        "strategy",
        "precision_at_k",
        "recall_at_k",
        "hit_at_k",
        "mrr",
        "ndcg_at_k",
        "retrieved_chunk_ids",
        "retrieved_scores",
        "retrieved_page_ranges",
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"


def test_sample_queries_dataset_loading():
    from src.app.streamlit_app import load_sample_queries_df

    df = load_sample_queries_df()
    assert df is not None, "Failed to load benchmark queries dataset"
    assert len(df) == 15
    assert set(df["pdf_id"].unique()) == {
        "attention_vaswani2017.pdf",
        "rag_lewis2020.pdf",
        "bert_devlin2018.pdf",
    }


def test_calculate_stats_function():
    from src.app.streamlit_app import calculate_stats

    empty_stats = calculate_stats([])
    assert empty_stats["Chunks"] == 0
    assert empty_stats["Mean Tokens"] == 0.0

    c1 = Chunk(chunk_id="c1", text="Sample 1", page_start=1, page_end=1, token_count=100, strategy="test")
    c2 = Chunk(chunk_id="c2", text="Sample 2", page_start=1, page_end=1, token_count=200, strategy="test")

    stats = calculate_stats([c1, c2])
    assert stats["Chunks"] == 2
    assert stats["Mean Tokens"] == 150.0
    assert stats["Min Tokens"] == 100
    assert stats["Max Tokens"] == 200


def test_strategy_map_and_callable_chunkers():
    from src.app.streamlit_app import STRATEGY_MAP
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    assert set(STRATEGY_MAP.keys()) == {"Fixed", "Recursive", "Sentence", "SDCA"}

    for name, chunk_fn in STRATEGY_MAP.items():
        chunks = chunk_fn(doc, tok)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
        assert chunks[0].token_count > 0


def test_get_available_sample_pdfs():
    from src.app.streamlit_app import get_available_sample_pdfs

    pdfs = get_available_sample_pdfs()
    assert len(pdfs) == 3
    assert "attention_vaswani2017.pdf" in pdfs
    assert "rag_lewis2020.pdf" in pdfs
    assert "bert_devlin2018.pdf" in pdfs


def test_retrieval_demo_pipeline_construction():
    chunks = [
        Chunk(chunk_id="c1", text="Attention is all you need.", page_start=1, page_end=1, token_count=6, strategy="test"),
        Chunk(chunk_id="c2", text="BERT bidirectional pretraining.", page_start=2, page_end=2, token_count=4, strategy="test"),
    ]
    embeddings = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ], dtype=np.float32)

    store = FAISSVectorStore(dimension=4)
    store.add_chunks(chunks, embeddings)

    query_vec = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    hits = store.search(query_vec, top_k=2)

    assert len(hits) == 2
    top_chunk, score, rank = hits[0]
    assert rank == 1
    assert top_chunk.chunk_id == "c1"
    assert pytest.approx(score, abs=1e-5) == 1.0


# ==============================================================================
# Phase 5.1: Interactive Research Laboratory Tests
# ==============================================================================

def test_available_strategies_contains_all_four():
    from src.app.comparison import AVAILABLE_STRATEGIES

    assert set(AVAILABLE_STRATEGIES) == {"Fixed", "Recursive", "Sentence", "SDCA"}


def test_comparison_dispatch_calls_correct_existing_algorithms():
    from src.app.comparison import run_chunking_strategy
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    for strat in ["Fixed", "Recursive", "Sentence", "SDCA"]:
        chunks = run_chunking_strategy(strat, doc, tok, target_tokens=400)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
        assert chunks[0].strategy == strat.lower()


def test_same_document_processed_by_all_four_strategies():
    from src.app.comparison import AVAILABLE_STRATEGIES, run_comparison
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    results = run_comparison(doc, AVAILABLE_STRATEGIES, tok, target_tokens=400)
    assert set(results.keys()) == set(AVAILABLE_STRATEGIES)
    for strat, chunks in results.items():
        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)


def test_extended_chunk_statistics_calculation():
    from src.app.comparison import calculate_extended_stats

    empty_stats = calculate_extended_stats([])
    assert empty_stats["Chunk Count"] == 0
    assert empty_stats["Mean Tokens"] == 0.0
    assert empty_stats["Mean Characters"] == 0.0

    c1 = Chunk(chunk_id="c1", text="Short text.", page_start=1, page_end=1, token_count=10, strategy="sdca")
    c2 = Chunk(chunk_id="c2", text="A somewhat longer sentence text.", page_start=1, page_end=1, token_count=30, strategy="sdca")

    stats = calculate_extended_stats([c1, c2])
    assert stats["Chunk Count"] == 2
    assert stats["Mean Tokens"] == 20.0
    assert stats["Median Tokens"] == 20.0
    assert stats["Min Tokens"] == 10
    assert stats["Max Tokens"] == 30
    assert stats["Std Dev"] == 10.0
    assert stats["Mean Characters"] == round((len(c1.text) + len(c2.text)) / 2, 2)


def test_comparison_output_contains_strategy_identifiers():
    from src.app.comparison import AVAILABLE_STRATEGIES, run_comparison
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    results = run_comparison(doc, AVAILABLE_STRATEGIES, tok)
    for strat in AVAILABLE_STRATEGIES:
        assert strat in results
        for c in results[strat]:
            assert c.strategy == strat.lower()
            assert c.chunk_id.startswith(strat.lower())


def test_retrieval_comparison_produces_results_for_all_selected_strategies():
    from src.app.comparison import AVAILABLE_STRATEGIES, run_retrieval_comparison
    from src.baselines.tokenization import RegexTokenizer

    class MockEmbeddingManager:
        def __init__(self):
            self.dimension = 4
            self.tokenizer = RegexTokenizer()

        def encode(self, texts, normalize_embeddings=True):
            vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
            for i in range(len(texts)):
                vectors[i, i % self.dimension] = 1.0
            return vectors

    doc = make_synthetic_document()
    mock_mgr = MockEmbeddingManager()

    results = run_retrieval_comparison(
        doc=doc,
        selected_strategies=AVAILABLE_STRATEGIES,
        query="neural network mechanism",
        top_k=2,
        embedding_mgr=mock_mgr,
        target_tokens=400,
    )

    assert set(results.keys()) == set(AVAILABLE_STRATEGIES)
    for strat, hits in results.items():
        assert len(hits) >= 1
        top_chunk, score, rank = hits[0]
        assert rank == 1
        assert isinstance(score, float)
        assert isinstance(top_chunk, Chunk)


def test_official_benchmark_files_integrity_unmodified():
    from pathlib import Path
    import hashlib

    summary_file = Path("experiments/results/experiment_summary.csv")
    retrieval_file = Path("experiments/results/retrieval_results.csv")
    queries_file = Path("data/queries/queries.csv")

    assert summary_file.is_file(), "experiment_summary.csv must exist"
    assert retrieval_file.is_file(), "retrieval_results.csv must exist"
    assert queries_file.is_file(), "queries.csv must exist"

    # Compute hashes
    h_sum1 = hashlib.sha256(summary_file.read_bytes()).hexdigest()
    h_ret1 = hashlib.sha256(retrieval_file.read_bytes()).hexdigest()
    h_que1 = hashlib.sha256(queries_file.read_bytes()).hexdigest()

    # Import and run app data loaders
    from src.app.streamlit_app import (
        load_official_benchmark_summary,
        load_official_retrieval_results,
        load_sample_queries_df,
    )

    _ = load_official_benchmark_summary()
    _ = load_official_retrieval_results()
    _ = load_sample_queries_df()

    # Re-verify hashes remain completely unchanged
    h_sum2 = hashlib.sha256(summary_file.read_bytes()).hexdigest()
    h_ret2 = hashlib.sha256(retrieval_file.read_bytes()).hexdigest()
    h_que2 = hashlib.sha256(queries_file.read_bytes()).hexdigest()

    assert h_sum1 == h_sum2, "experiment_summary.csv was modified!"
    assert h_ret1 == h_ret2, "retrieval_results.csv was modified!"
    assert h_que1 == h_que2, "queries.csv was modified!"


def test_invalid_strategy_dispatch_raises_error():
    from src.app.comparison import run_chunking_strategy
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    with pytest.raises(ValueError, match="Unknown chunking strategy"):
        run_chunking_strategy("SemanticChunking", doc, tok)


def test_v2_benchmark_data_loading():
    from src.app.streamlit_app import (
        load_v2_benchmark_summary,
        load_v2_retrieval_results,
    )

    df_sum = load_v2_benchmark_summary()
    assert df_sum is not None, "Failed to load V2 benchmark summary"
    assert len(df_sum) == 5, f"Expected 5 strategies in V2 summary, got {len(df_sum)}"

    strategies = set(df_sum["strategy"].str.lower())
    assert strategies == {"fixed", "recursive", "sentence", "sdca_v1", "sdca_v2"}

    # Verify key V2 metrics exist
    v2_row = df_sum[df_sum["strategy"] == "sdca_v2"].iloc[0]
    assert v2_row["mrr"] > 0.75
    assert v2_row["mean_ndcg_at_5"] > 0.80

    df_det = load_v2_retrieval_results()
    assert df_det is not None, "Failed to load V2 retrieval results"
    assert len(df_det) == 75, f"Expected 75 query results (15 queries * 5 strategies), got {len(df_det)}"


def test_sdca_v2_app_chunking_and_retrieval():
    from src.app.comparison import (
        ALL_AVAILABLE_STRATEGIES,
        run_chunking_strategy,
        run_retrieval_comparison,
    )
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    # Test chunking dispatch for SDCA V2
    chunks = run_chunking_strategy("SDCA V2", doc, tok, target_tokens=400)
    assert len(chunks) >= 1
    assert chunks[0].strategy == "sdca_v2"
    assert "section_path" in chunks[0].metadata

    # Test retrieval with ALL_AVAILABLE_STRATEGIES
    class MockEmbeddingManager:
        def __init__(self):
            self.dimension = 4
            self.tokenizer = tok

        def encode(self, texts, normalize_embeddings=True):
            return np.ones((len(texts), self.dimension), dtype=np.float32)

    mock_mgr = MockEmbeddingManager()
    res = run_retrieval_comparison(
        doc=doc,
        selected_strategies=ALL_AVAILABLE_STRATEGIES,
        query="neural network",
        top_k=2,
        embedding_mgr=mock_mgr,
    )
    assert "SDCA V2" in res
    assert len(res["SDCA V2"]) >= 1


def test_render_retrieval_chunk_card_helper():
    from src.app.streamlit_app import render_retrieval_chunk_card

    c1 = Chunk(
        chunk_id="sdca_v2_1",
        text="Parent-heading context aids passage interpretation in RAG.",
        page_start=2,
        page_end=3,
        token_count=12,
        strategy="sdca_v2",
        metadata={"section_path": "2. Background > 2.1 Context", "section_title": "2.1 Context"},
        retrieval_text="[Section: 2. Background > 2.1 Context]\n\nParent-heading context aids passage interpretation in RAG.",
    )

    # Should execute cleanly without error for rank 1 (default_expanded=True)
    render_retrieval_chunk_card(
        chunk=c1,
        score=0.8850,
        rank=1,
        strategy="SDCA (V2)",
        key_prefix="test_exp",
        default_expanded=True,
    )

    # Should execute cleanly without error for rank 2 (default_expanded=False)
    c2 = Chunk(
        chunk_id="fixed_1",
        text="A simple fixed chunk.",
        page_start=1,
        page_end=1,
        token_count=5,
        strategy="fixed",
    )
    render_retrieval_chunk_card(
        chunk=c2,
        score=0.6500,
        rank=2,
        strategy="Fixed",
        key_prefix="test_col",
        default_expanded=False,
    )


def test_all_five_strategies_retrieval_lab_execution():
    from src.app.comparison import run_retrieval_comparison
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    class MockEmbeddingManager:
        def __init__(self):
            self.dimension = 4
            self.tokenizer = tok

        def encode(self, texts, normalize_embeddings=True):
            return np.ones((len(texts), self.dimension), dtype=np.float32)

    all_five = ["Fixed", "Recursive", "Sentence", "SDCA (V1)", "SDCA (V2)"]
    mock_mgr = MockEmbeddingManager()

    res = run_retrieval_comparison(
        doc=doc,
        selected_strategies=all_five,
        query="attention mechanisms",
        top_k=3,
        embedding_mgr=mock_mgr,
    )

    assert set(res.keys()) == set(all_five)
    for strat in all_five:
        hits = res[strat]
        assert len(hits) >= 1
        top_chunk, score, rank = hits[0]
        assert rank == 1
        assert isinstance(score, float)
        assert isinstance(top_chunk, Chunk)


def test_generate_llm_answer_without_key():
    from src.app.comparison import generate_llm_answer
    c = Chunk(chunk_id="c1", text="Test passage text.", page_start=1, page_end=1, token_count=5, strategy="sdca")
    res = generate_llm_answer("query", [c], api_key=None)
    assert res["error"] == "MISSING_API_KEY" or "GEMINI_API_KEY" in res["answer"]


def test_sdca_stair_in_retrieval_lab():
    from src.app.comparison import run_retrieval_comparison
    from src.baselines.tokenization import RegexTokenizer

    doc = make_synthetic_document()
    tok = RegexTokenizer()

    class MockEmbeddingManager:
        def __init__(self):
            self.dimension = 4
            self.tokenizer = tok

        def encode(self, texts, normalize_embeddings=True):
            return np.ones((len(texts), self.dimension), dtype=np.float32)

    mock_mgr = MockEmbeddingManager()
    res = run_retrieval_comparison(
        doc=doc,
        selected_strategies=["Recursive", "SDCA (STAIR)"],
        query="neural mechanism",
        top_k=2,
        embedding_mgr=mock_mgr,
    )
    assert "SDCA (STAIR)" in res
    assert len(res["SDCA (STAIR)"]) >= 1



"""Unit tests for Phase 4 experiments and IR metrics module."""

import pytest

from src.baselines.models import Chunk
from src.experiments.metrics import (
    evaluate_query_retrieval,
    hit_at_k,
    is_chunk_relevant,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from src.experiments.runner import (
    calculate_chunk_statistics,
    load_benchmark_queries,
)


def make_test_chunk(chunk_id: str, page_start: int, page_end: int, token_count: int = 100) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        text=f"Text for {chunk_id}",
        page_start=page_start,
        page_end=page_end,
        token_count=token_count,
        strategy="test",
    )


def test_is_chunk_relevant():
    chunk = make_test_chunk("c1", page_start=3, page_end=5)

    assert is_chunk_relevant(chunk, [4]) is True
    assert is_chunk_relevant(chunk, [3]) is True
    assert is_chunk_relevant(chunk, [5]) is True
    assert is_chunk_relevant(chunk, [1, 2]) is False
    assert is_chunk_relevant(chunk, [6, 7]) is False
    assert is_chunk_relevant(chunk, []) is False


def test_precision_at_k():
    c1 = make_test_chunk("c1", 1, 1)  # rel for [1]
    c2 = make_test_chunk("c2", 2, 2)  # not rel
    c3 = make_test_chunk("c3", 1, 2)  # rel for [1]
    c4 = make_test_chunk("c4", 3, 3)  # not rel
    c5 = make_test_chunk("c5", 4, 4)  # not rel

    chunks = [c1, c2, c3, c4, c5]
    expected = [1]

    assert precision_at_k(chunks, expected, k=5) == 2.0 / 5.0
    assert precision_at_k(chunks, expected, k=3) == 2.0 / 3.0
    assert precision_at_k(chunks, expected, k=1) == 1.0
    assert precision_at_k(chunks, [99], k=5) == 0.0


def test_recall_at_k():
    c1 = make_test_chunk("c1", 1, 1)
    c2 = make_test_chunk("c2", 2, 2)
    c3 = make_test_chunk("c3", 5, 5)

    chunks = [c1, c2, c3]
    expected = [1, 2, 3]  # 3 expected pages

    # Top 2 chunks cover pages 1 and 2 (2/3)
    assert pytest.approx(recall_at_k(chunks, expected, k=2), abs=1e-4) == 2.0 / 3.0
    # Top 1 chunk covers page 1 (1/3)
    assert pytest.approx(recall_at_k(chunks, expected, k=1), abs=1e-4) == 1.0 / 3.0
    # Empty expected pages
    assert recall_at_k(chunks, [], k=2) == 0.0


def test_hit_at_k():
    c_rel = make_test_chunk("c1", 2, 2)
    c_irrel = make_test_chunk("c2", 5, 5)

    assert hit_at_k([c_rel, c_irrel], [2], k=2) == 1.0
    assert hit_at_k([c_irrel, c_irrel], [2], k=2) == 0.0
    assert hit_at_k([c_irrel, c_rel], [2], k=1) == 0.0  # k=1 misses c_rel at pos 2


def test_reciprocal_rank():
    c_rel = make_test_chunk("c1", 3, 3)
    c_irrel = make_test_chunk("c2", 1, 1)

    # Relevant at rank 1 -> RR = 1.0
    assert reciprocal_rank([c_rel, c_irrel], [3], k=2) == 1.0
    # Relevant at rank 2 -> RR = 0.5
    assert reciprocal_rank([c_irrel, c_rel], [3], k=2) == 0.5
    # Relevant not in top 1 -> RR = 0.0
    assert reciprocal_rank([c_irrel, c_rel], [3], k=1) == 0.0
    # No relevant chunk -> 0.0
    assert reciprocal_rank([c_irrel, c_irrel], [3], k=2) == 0.0


def test_ndcg_at_k():
    c_rel = make_test_chunk("c1", 4, 4)
    c_irrel = make_test_chunk("c2", 1, 1)

    # Perfect ranking: relevant item at rank 1
    assert pytest.approx(ndcg_at_k([c_rel, c_irrel], [4], k=2), abs=1e-4) == 1.0
    # Inverted ranking: relevant item at rank 2
    ndcg_inverted = ndcg_at_k([c_irrel, c_rel], [4], k=2)
    assert 0.0 < ndcg_inverted < 1.0
    # No relevant item
    assert ndcg_at_k([c_irrel, c_irrel], [4], k=2) == 0.0


def test_evaluate_query_retrieval_integration():
    c1 = make_test_chunk("c1", 4, 4)
    c2 = make_test_chunk("c2", 1, 1)

    res = evaluate_query_retrieval(
        query_id="Q01",
        pdf_id="doc1.pdf",
        question="What is attention?",
        expected_pages=[4],
        strategy="sdca",
        retrieved_chunks=[c1, c2],
        retrieved_scores=[0.85, 0.40],
        k=2,
    )

    assert res.query_id == "Q01"
    assert res.precision == 0.5
    assert res.recall == 1.0
    assert res.hit == 1.0
    assert res.reciprocal_rank == 1.0
    assert pytest.approx(res.ndcg, abs=1e-4) == 1.0


def test_load_benchmark_queries():
    queries = load_benchmark_queries("data/queries/queries.csv")
    assert len(queries) == 15
    for q in queries:
        assert q["query_id"].startswith("Q")
        assert q["pdf_id"].endswith(".pdf")
        assert len(q["question"]) > 10
        assert len(q["expected_pages"]) >= 1
        assert all(isinstance(p, int) for p in q["expected_pages"])


def test_calculate_chunk_statistics():
    empty_stats = calculate_chunk_statistics([])
    assert empty_stats["total_chunks"] == 0

    chunks = [
        make_test_chunk("c1", 1, 1, token_count=100),
        make_test_chunk("c2", 1, 1, token_count=200),
        make_test_chunk("c3", 1, 1, token_count=300),
    ]
    stats = calculate_chunk_statistics(chunks)
    assert stats["total_chunks"] == 3
    assert stats["mean_tokens"] == 200.0
    assert stats["median_tokens"] == 200.0
    assert stats["min_tokens"] == 100
    assert stats["max_tokens"] == 300
    assert stats["std_tokens"] > 0

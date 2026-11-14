"""Evaluation metrics for information retrieval in RAG.

Calculates:
- Precision@K: Fraction of top-K chunks that are relevant.
- Recall@K: Fraction of ground-truth target pages covered by top-K retrieved chunks.
- Hit@K: Binary indicator (1.0 or 0.0) whether any relevant chunk was retrieved in top-K.
- MRR (Mean Reciprocal Rank): Reciprocal rank (1 / rank) of the first relevant chunk.
- NDCG@K: Normalized Discounted Cumulative Gain over top-K positions.
"""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from src.baselines.models import Chunk


def is_chunk_relevant(chunk: Chunk, expected_pages: List[int]) -> bool:
    """Evaluates whether a chunk overlaps with any ground-truth expected page.

    Relevance Condition:
    A chunk is deemed relevant if:
        exists p in expected_pages such that chunk.page_start <= p <= chunk.page_end

    Args:
        chunk: Retrieved Chunk instance.
        expected_pages: 1-based page numbers marked as relevant ground truth.

    Returns:
        True if the chunk covers at least one expected page, False otherwise.
    """
    if not expected_pages:
        return False
    return any(chunk.page_start <= p <= chunk.page_end for p in expected_pages)


def precision_at_k(
    retrieved_chunks: List[Chunk],
    expected_pages: List[int],
    k: int = 5,
) -> float:
    """Computes Precision@K.

    Precision@K = (Number of relevant chunks in top-K) / K
    """
    if k <= 0:
        return 0.0
    top_k_chunks = retrieved_chunks[:k]
    relevant_count = sum(1 for c in top_k_chunks if is_chunk_relevant(c, expected_pages))
    return float(relevant_count) / float(k)


def recall_at_k(
    retrieved_chunks: List[Chunk],
    expected_pages: List[int],
    k: int = 5,
) -> float:
    """Computes Recall@K (page coverage recall).

    Recall@K = |covered_expected_pages_in_top_k| / |expected_pages|
    """
    if not expected_pages:
        return 0.0
    top_k_chunks = retrieved_chunks[:k]
    covered_pages: Set[int] = set()
    for c in top_k_chunks:
        for p in expected_pages:
            if c.page_start <= p <= c.page_end:
                covered_pages.add(p)
    return float(len(covered_pages)) / float(len(expected_pages))


def hit_at_k(
    retrieved_chunks: List[Chunk],
    expected_pages: List[int],
    k: int = 5,
) -> float:
    """Computes Hit@K (1.0 if any relevant chunk is in top-K, else 0.0)."""
    top_k_chunks = retrieved_chunks[:k]
    for c in top_k_chunks:
        if is_chunk_relevant(c, expected_pages):
            return 1.0
    return 0.0


def reciprocal_rank(
    retrieved_chunks: List[Chunk],
    expected_pages: List[int],
    k: int = 5,
) -> float:
    """Computes Reciprocal Rank (1 / rank of first relevant chunk, or 0.0)."""
    top_k_chunks = retrieved_chunks[:k]
    for rank_idx, c in enumerate(top_k_chunks, start=1):
        if is_chunk_relevant(c, expected_pages):
            return 1.0 / float(rank_idx)
    return 0.0


def ndcg_at_k(
    retrieved_chunks: List[Chunk],
    expected_pages: List[int],
    k: int = 5,
) -> float:
    """Computes Normalized Discounted Cumulative Gain at rank K (binary relevance)."""
    if k <= 0:
        return 0.0
    top_k_chunks = retrieved_chunks[:k]
    rel_scores = [1.0 if is_chunk_relevant(c, expected_pages) else 0.0 for c in top_k_chunks]

    # DCG = sum_i (rel_i / log2(i + 1))
    dcg = 0.0
    for idx, r in enumerate(rel_scores, start=1):
        if r > 0.0:
            dcg += r / math.log2(idx + 1)

    # Ideal ranking places all 1.0s first
    ideal_scores = sorted(rel_scores, reverse=True)
    idcg = 0.0
    for idx, r in enumerate(ideal_scores, start=1):
        if r > 0.0:
            idcg += r / math.log2(idx + 1)

    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


@dataclass
class QueryEvaluationResult:
    """Stores detailed retrieval results and metrics for a single query."""

    query_id: str
    pdf_id: str
    question: str
    expected_pages: List[int]
    strategy: str
    top_k: int
    retrieved_chunks: List[Chunk] = field(default_factory=list)
    retrieved_scores: List[float] = field(default_factory=list)
    precision: float = 0.0
    recall: float = 0.0
    hit: float = 0.0
    reciprocal_rank: float = 0.0
    ndcg: float = 0.0


def evaluate_query_retrieval(
    query_id: str,
    pdf_id: str,
    question: str,
    expected_pages: List[int],
    strategy: str,
    retrieved_chunks: List[Chunk],
    retrieved_scores: List[float],
    k: int = 5,
) -> QueryEvaluationResult:
    """Evaluates all metrics for a single query retrieval."""
    p_k = precision_at_k(retrieved_chunks, expected_pages, k=k)
    r_k = recall_at_k(retrieved_chunks, expected_pages, k=k)
    h_k = hit_at_k(retrieved_chunks, expected_pages, k=k)
    rr = reciprocal_rank(retrieved_chunks, expected_pages, k=k)
    ndcg = ndcg_at_k(retrieved_chunks, expected_pages, k=k)

    return QueryEvaluationResult(
        query_id=query_id,
        pdf_id=pdf_id,
        question=question,
        expected_pages=expected_pages,
        strategy=strategy,
        top_k=k,
        retrieved_chunks=retrieved_chunks[:k],
        retrieved_scores=retrieved_scores[:k],
        precision=p_k,
        recall=r_k,
        hit=h_k,
        reciprocal_rank=rr,
        ndcg=ndcg,
    )

"""Experiments package for SDCA retrieval benchmarking.

Contains metrics evaluation, benchmark query runner, and experiment orchestration.
"""

from src.experiments.metrics import (
    QueryEvaluationResult,
    evaluate_query_retrieval,
    hit_at_k,
    is_chunk_relevant,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from src.experiments.runner import (
    ControlledExperimentRunner,
    calculate_chunk_statistics,
    load_benchmark_queries,
)

__all__ = [
    "QueryEvaluationResult",
    "evaluate_query_retrieval",
    "hit_at_k",
    "is_chunk_relevant",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "ControlledExperimentRunner",
    "calculate_chunk_statistics",
    "load_benchmark_queries",
]

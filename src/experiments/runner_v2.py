"""Controlled Retrieval Experiment Runner for SDCA V2.

Compares 5 strategies under strict Ceteris Paribus conditions:
1. fixed
2. recursive
3. sentence
4. sdca_v1
5. sdca_v2

Enforces strict experimental invariance:
- Same 3 landmark academic PDFs (50 pages).
- Same 15 domain queries and ground truth from data/queries/queries.csv.
- Same Sentence Transformers model (all-MiniLM-L6-v2, 384 dimensions).
- Same model tokenizer and 400-token target.
- Same FAISS IndexFlatIP (exact Cosine Similarity via L2 normalization).
- Same Top-K = 5.
- Same IR metrics: Precision@5, Recall@5, Hit@5, MRR, and NDCG@5.

Results are persisted to `experiments/results_v2/` without touching Phase 4 results.
"""

import csv
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np

# Prevent OpenMP runtime conflict on macOS
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from src.baselines.fixed import chunk_fixed
from src.baselines.models import Chunk
from src.baselines.recursive import chunk_recursive
from src.baselines.sentence import chunk_sentence
from src.experiments.metrics import (
    QueryEvaluationResult,
    evaluate_query_retrieval,
)
from src.experiments.runner import (
    calculate_chunk_statistics,
    load_benchmark_queries,
)
from src.extraction.models import Document
from src.extraction.pdf_parser import load_pdf
from src.retrieval.embeddings import EmbeddingManager, ModelTokenizer
from src.retrieval.faiss_store import FAISSVectorStore
from src.sdca.chunker import chunk_sdca
from src.sdca.v2.chunker import chunk_sdca_v2

STRATEGY_CHUNKERS_V2: Dict[str, Callable[[Document, Any], List[Chunk]]] = {
    "fixed": lambda doc, tok: chunk_fixed(doc, target_tokens=400, overlap_tokens=50, tokenizer=tok),
    "recursive": lambda doc, tok: chunk_recursive(doc, target_tokens=400, tokenizer=tok),
    "sentence": lambda doc, tok: chunk_sentence(doc, target_tokens=400, tokenizer=tok),
    "sdca_v1": lambda doc, tok: chunk_sdca(doc, target_tokens=400, min_tokens=200, max_tokens=600, tokenizer=tok),
    "sdca_v2": lambda doc, tok: chunk_sdca_v2(doc, target_tokens=400, min_tokens=200, max_tokens=600, tokenizer=tok),
}


class ControlledExperimentRunnerV2:
    """Orchestrates controlled retrieval experiments across all 5 chunking strategies."""

    def __init__(
        self,
        raw_pdfs_dir: str = "data/raw_pdfs",
        queries_file: str = "data/queries/queries.csv",
        results_dir: str = "experiments/results_v2",
        embedding_model_name: str = EmbeddingManager.DEFAULT_MODEL_NAME,
        top_k: int = 5,
    ):
        self.raw_pdfs_dir = Path(raw_pdfs_dir)
        self.queries_file = Path(queries_file)
        self.results_dir = Path(results_dir)
        self.top_k = top_k

        # Initialize shared embedding manager and model tokenizer
        self.embedding_manager = EmbeddingManager(model_name=embedding_model_name)
        self.tokenizer = self.embedding_manager.tokenizer

    def load_documents(self, pdf_names: Optional[List[str]] = None) -> Dict[str, Document]:
        """Loads and parses PDF documents using Phase 1 PyMuPDF parser."""
        if not self.raw_pdfs_dir.is_dir():
            raise FileNotFoundError(f"Raw PDFs directory not found: {self.raw_pdfs_dir}")

        if pdf_names is None:
            pdf_files = sorted(self.raw_pdfs_dir.glob("*.pdf"))
        else:
            pdf_files = [self.raw_pdfs_dir / name for name in pdf_names]

        documents: Dict[str, Document] = {}
        for pdf_path in pdf_files:
            if not pdf_path.is_file():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            doc = load_pdf(str(pdf_path))
            documents[pdf_path.name] = doc

        return documents

    def generate_chunks_for_strategy(
        self,
        strategy: str,
        documents: Dict[str, Document],
    ) -> Dict[str, List[Chunk]]:
        """Applies a specific chunking strategy across all loaded documents."""
        if strategy not in STRATEGY_CHUNKERS_V2:
            raise ValueError(
                f"Unknown strategy: '{strategy}'. Choose from {list(STRATEGY_CHUNKERS_V2.keys())}"
            )

        chunk_fn = STRATEGY_CHUNKERS_V2[strategy]
        doc_chunks: Dict[str, List[Chunk]] = {}

        for pdf_id, doc in documents.items():
            chunks = chunk_fn(doc, self.tokenizer)
            for c in chunks:
                c.metadata["pdf_id"] = pdf_id
            doc_chunks[pdf_id] = chunks

        return doc_chunks

    def run_strategy_benchmark(
        self,
        strategy: str,
        documents: Dict[str, Document],
        queries: List[Dict[str, Any]],
    ) -> Tuple[List[Chunk], Dict[str, float], List[QueryEvaluationResult]]:
        """Runs end-to-end benchmark for one strategy: chunk -> embed -> index -> retrieve -> eval."""
        # 1. Chunk documents using common tokenizer
        doc_chunks_map = self.generate_chunks_for_strategy(strategy, documents)
        all_chunks: List[Chunk] = []
        for chunks in doc_chunks_map.values():
            all_chunks.extend(chunks)

        chunk_stats = calculate_chunk_statistics(all_chunks)

        # 2. Embed chunk text using structure-aware retrieval representation when available
        chunk_texts = [
            getattr(c, "retrieval_text", None) or c.metadata.get("retrieval_text") or c.text
            for c in all_chunks
        ]
        chunk_embeddings = self.embedding_manager.encode(
            chunk_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # 3. Index in FAISS
        vector_store = FAISSVectorStore(dimension=self.embedding_manager.dimension)
        vector_store.add_chunks(all_chunks, chunk_embeddings)

        # 4. Filter queries relevant to loaded documents
        active_queries = [q for q in queries if q["pdf_id"] in documents]

        # 5. Retrieve and evaluate each query
        query_results: List[QueryEvaluationResult] = []
        for q in active_queries:
            q_emb = self.embedding_manager.encode(
                [q["question"]],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            search_hits = vector_store.search(q_emb[0], top_k=self.top_k)

            # Filter to chunks belonging to this query's document for controlled per-document retrieval
            doc_hits = [(c, score) for c, score, rank in search_hits if c.metadata.get("pdf_id") == q["pdf_id"]]

            retrieved_chunks = [c for c, _ in doc_hits]
            retrieved_scores = [score for _, score in doc_hits]

            eval_res = evaluate_query_retrieval(
                query_id=q["query_id"],
                pdf_id=q["pdf_id"],
                question=q["question"],
                expected_pages=q["expected_pages"],
                strategy=strategy,
                retrieved_chunks=retrieved_chunks,
                retrieved_scores=retrieved_scores,
                k=self.top_k,
            )
            query_results.append(eval_res)

        return all_chunks, chunk_stats, query_results

    def run_all_experiments(
        self,
        strategies: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[QueryEvaluationResult]]:
        """Executes full benchmark across all 5 strategies and writes results to experiments/results_v2/."""
        if strategies is None:
            strategies = ["fixed", "recursive", "sentence", "sdca_v1", "sdca_v2"]

        self.results_dir.mkdir(parents=True, exist_ok=True)

        documents = self.load_documents()
        queries = load_benchmark_queries(self.queries_file)

        summary_rows: List[Dict[str, Any]] = []
        all_query_results: List[QueryEvaluationResult] = []

        for strat in strategies:
            print(f"Running controlled evaluation for strategy: {strat.upper()}...")
            chunks, stats, q_results = self.run_strategy_benchmark(strat, documents, queries)
            all_query_results.extend(q_results)

            mean_prec = float(np.mean([qr.precision for qr in q_results]))
            mean_rec = float(np.mean([qr.recall for qr in q_results]))
            hit_rate = float(np.mean([qr.hit for qr in q_results]))
            mrr_val = float(np.mean([qr.reciprocal_rank for qr in q_results]))
            mean_ndcg = float(np.mean([qr.ndcg for qr in q_results]))

            summary_rows.append({
                "strategy": strat,
                "total_chunks": stats["total_chunks"],
                "mean_tokens": round(stats["mean_tokens"], 2),
                "median_tokens": round(stats["median_tokens"], 2),
                "min_tokens": stats["min_tokens"],
                "max_tokens": stats["max_tokens"],
                "std_tokens": round(stats["std_tokens"], 2),
                "mean_precision_at_5": round(mean_prec, 4),
                "mean_recall_at_5": round(mean_rec, 4),
                "hit_rate_at_5": round(hit_rate, 4),
                "mrr": round(mrr_val, 4),
                "mean_ndcg_at_5": round(mean_ndcg, 4),
            })

        # Save summary CSV in experiments/results_v2/
        summary_path = self.results_dir / "experiment_summary.csv"
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

        # Save detailed results CSV in experiments/results_v2/
        detailed_path = self.results_dir / "retrieval_results.csv"
        with open(detailed_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
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
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for qr in all_query_results:
                chunk_ids = ";".join(c.chunk_id for c in qr.retrieved_chunks)
                scores = ";".join(f"{s:.4f}" for s in qr.retrieved_scores)
                pages = ";".join(f"{c.page_start}-{c.page_end}" for c in qr.retrieved_chunks)
                writer.writerow({
                    "query_id": qr.query_id,
                    "pdf_id": qr.pdf_id,
                    "strategy": qr.strategy,
                    "precision_at_k": round(qr.precision, 4),
                    "recall_at_k": round(qr.recall, 4),
                    "hit_at_k": round(qr.hit, 4),
                    "mrr": round(qr.reciprocal_rank, 4),
                    "ndcg_at_k": round(qr.ndcg, 4),
                    "retrieved_chunk_ids": chunk_ids,
                    "retrieved_scores": scores,
                    "retrieved_page_ranges": pages,
                })

        return summary_rows, all_query_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SDCA V2 Controlled Experiment Runner")
    parser.add_argument("--model", type=str, default=EmbeddingManager.DEFAULT_MODEL_NAME, help="SentenceTransformer model")
    args = parser.parse_args()

    runner = ControlledExperimentRunnerV2(embedding_model_name=args.model)
    print("=== EXECUTING CONTROLLED RETRIEVAL EXPERIMENTS (ALL 5 STRATEGIES) ===")
    summary, _ = runner.run_all_experiments()

    print("\n=== EXPERIMENTAL SUMMARY RESULTS (V2 BENCHMARK) ===")
    print(f"{'Strategy':<10} | {'Chunks':<6} | {'MeanTok':<8} | {'StdTok':<7} | {'P@5':<7} | {'R@5':<7} | {'Hit@5':<7} | {'MRR':<7} | {'NDCG@5':<7}")
    print("-" * 92)
    for row in summary:
        print(
            f"{row['strategy']:<10} | {row['total_chunks']:<6} | {row['mean_tokens']:<8.1f} | {row['std_tokens']:<7.1f} | "
            f"{row['mean_precision_at_5']:<7.4f} | {row['mean_recall_at_5']:<7.4f} | "
            f"{row['hit_rate_at_5']:<7.4f} | {row['mrr']:<7.4f} | {row['mean_ndcg_at_5']:<7.4f}"
        )
    print("\nResults persisted to experiments/results_v2/")


if __name__ == "__main__":
    main()

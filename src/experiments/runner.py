"""Controlled Retrieval Experiment Runner.

Enforces Ceteris Paribus experimental controls:
- Identical documents loaded via Phase 1 PyMuPDF parser.
- Identical pre-trained embedding model and tokenizer across ALL chunking strategies.
- Identical FAISS index configuration (IndexFlatIP with normalized vectors).
- Identical Top-K retrieval cutoff (K=5).
- Identical benchmark queries, ground truth, and evaluation metrics.
- The ONLY changing independent variable is the chunking strategy.
"""

import csv
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np

from src.baselines.fixed import chunk_fixed
from src.baselines.models import Chunk
from src.baselines.recursive import chunk_recursive
from src.baselines.sentence import chunk_sentence
from src.experiments.metrics import (
    QueryEvaluationResult,
    evaluate_query_retrieval,
)
from src.extraction.models import Document
from src.extraction.pdf_parser import load_pdf
from src.retrieval.embeddings import EmbeddingManager, ModelTokenizer
from src.retrieval.faiss_store import FAISSVectorStore
from src.sdca.chunker import chunk_sdca


STRATEGY_CHUNKERS = {
    "fixed": lambda doc, tok: chunk_fixed(doc, target_tokens=400, overlap_tokens=50, tokenizer=tok),
    "recursive": lambda doc, tok: chunk_recursive(doc, target_tokens=400, tokenizer=tok),
    "sentence": lambda doc, tok: chunk_sentence(doc, target_tokens=400, tokenizer=tok),
    "sdca": lambda doc, tok: chunk_sdca(doc, target_tokens=400, min_tokens=200, max_tokens=600, tokenizer=tok),
}


def load_benchmark_queries(csv_path: Union[str, Path] = "data/queries/queries.csv") -> List[Dict[str, Any]]:
    """Loads benchmark queries and parses comma-separated expected pages.

    Returns:
        List of dicts: [
            {"query_id": str, "pdf_id": str, "question": str, "expected_pages": List[int]},
            ...
        ]
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Query file not found at: {path}")

    queries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pages_raw = row["expected_pages"].strip().strip('"').strip("'")
            expected_pages = [int(p.strip()) for p in pages_raw.split(",") if p.strip()]
            queries.append({
                "query_id": row["query_id"].strip(),
                "pdf_id": row["pdf_id"].strip(),
                "question": row["question"].strip(),
                "expected_pages": expected_pages,
            })
    return queries


def calculate_chunk_statistics(chunks: List[Chunk]) -> Dict[str, float]:
    """Calculates descriptive token statistics for a set of chunks."""
    if not chunks:
        return {
            "total_chunks": 0,
            "mean_tokens": 0.0,
            "median_tokens": 0.0,
            "min_tokens": 0,
            "max_tokens": 0,
            "std_tokens": 0.0,
        }

    tokens = [c.token_count for c in chunks]
    return {
        "total_chunks": len(chunks),
        "mean_tokens": float(np.mean(tokens)),
        "median_tokens": float(np.median(tokens)),
        "min_tokens": int(np.min(tokens)),
        "max_tokens": int(np.max(tokens)),
        "std_tokens": float(np.std(tokens)),
    }


class ControlledExperimentRunner:
    """Orchestrates controlled retrieval experiments across all 4 chunking strategies."""

    def __init__(
        self,
        raw_pdfs_dir: str = "data/raw_pdfs",
        queries_file: str = "data/queries/queries.csv",
        results_dir: str = "experiments/results",
        embedding_model_name: str = EmbeddingManager.DEFAULT_MODEL_NAME,
        top_k: int = 5,
    ):
        self.raw_pdfs_dir = Path(raw_pdfs_dir)
        self.queries_file = Path(queries_file)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.top_k = top_k

        # Initialize single embedding manager providing model & common tokenizer
        self.embedding_manager = EmbeddingManager(model_name=embedding_model_name)
        self.tokenizer = self.embedding_manager.tokenizer

    def load_documents(self, pdf_filenames: Optional[List[str]] = None) -> Dict[str, Document]:
        """Loads and extracts specified PDFs using Phase 1 PyMuPDF parser."""
        if pdf_filenames is None:
            pdf_files = sorted(list(self.raw_pdfs_dir.glob("*.pdf")))
        else:
            pdf_files = [self.raw_pdfs_dir / fn for fn in pdf_filenames]

        documents: Dict[str, Document] = {}
        for pdf_path in pdf_files:
            if pdf_path.is_file():
                doc = load_pdf(str(pdf_path))
                documents[pdf_path.name] = doc

        if not documents:
            raise FileNotFoundError(f"No PDF documents found in {self.raw_pdfs_dir}")

        return documents

    def generate_chunks_for_strategy(
        self,
        strategy: str,
        documents: Dict[str, Document],
    ) -> Dict[str, List[Chunk]]:
        """Generates chunks for all documents using the specified strategy and model tokenizer.

        Returns:
            Dict mapping pdf_id to list of Chunk instances.
        """
        if strategy not in STRATEGY_CHUNKERS:
            raise ValueError(f"Unknown strategy: '{strategy}'. Choose from {list(STRATEGY_CHUNKERS.keys())}")

        chunk_fn = STRATEGY_CHUNKERS[strategy]
        doc_chunks: Dict[str, List[Chunk]] = {}

        for pdf_id, doc in documents.items():
            chunks = chunk_fn(doc, self.tokenizer)
            # Tag chunk metadata with pdf_id if not present
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

        # 2. Embed chunk text
        chunk_texts = [c.text for c in all_chunks]
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
            q_emb = self.embedding_manager.encode([q["question"]], normalize_embeddings=True)
            search_hits = vector_store.search(q_emb[0], top_k=self.top_k)

            # Filter to chunks belonging to this query's document for controlled per-document retrieval
            # or retain corpus-wide retrieval if searching full corpus.
            # In standard benchmark, query targets its specific document's index.
            # Here, we evaluate across the indexed corpus chunks for this document:
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
        pdf_filenames: Optional[List[str]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[QueryEvaluationResult]]:
        """Runs the complete comparative benchmark across all 4 strategies."""
        documents = self.load_documents(pdf_filenames)
        queries = load_benchmark_queries(self.queries_file)

        summary_rows: List[Dict[str, Any]] = []
        all_query_results: List[QueryEvaluationResult] = []

        for strategy in ["fixed", "recursive", "sentence", "sdca"]:
            all_chunks, stats, q_results = self.run_strategy_benchmark(strategy, documents, queries)
            all_query_results.extend(q_results)

            # Calculate aggregate metrics
            mean_prec = float(np.mean([qr.precision for qr in q_results])) if q_results else 0.0
            mean_rec = float(np.mean([qr.recall for qr in q_results])) if q_results else 0.0
            hit_rate = float(np.mean([qr.hit for qr in q_results])) if q_results else 0.0
            mrr_val = float(np.mean([qr.reciprocal_rank for qr in q_results])) if q_results else 0.0
            mean_ndcg = float(np.mean([qr.ndcg for qr in q_results])) if q_results else 0.0

            summary_rows.append({
                "strategy": strategy,
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

        # Save summary CSV
        summary_path = self.results_dir / "experiment_summary.csv"
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

        # Save detailed results CSV
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

    def run_smoke_test(self) -> List[QueryEvaluationResult]:
        """Executes a fast smoke test across 1 PDF and 1 query for all 4 strategies."""
        print("=== RUNNING PHASE 4 SMOKE TEST (1 PDF, 1 Query, 4 Strategies) ===")
        doc_map = self.load_documents(["attention_vaswani2017.pdf"])
        queries = load_benchmark_queries(self.queries_file)
        smoke_query = [q for q in queries if q["query_id"] == "Q01"]

        results: List[QueryEvaluationResult] = []
        for strat in ["fixed", "recursive", "sentence", "sdca"]:
            chunks, stats, q_res = self.run_strategy_benchmark(strat, doc_map, smoke_query)
            if q_res:
                results.append(q_res[0])
                print(
                    f"[{strat.upper():<9}] Chunks={stats['total_chunks']:<3} | "
                    f"MeanTokens={stats['mean_tokens']:<5.1f} | "
                    f"Top-1 Score={q_res[0].retrieved_scores[0]:.4f} | "
                    f"Hit@5={q_res[0].hit:.1f} | MRR={q_res[0].reciprocal_rank:.2f}"
                )

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SDCA Controlled Experiment Runner")
    parser.add_argument("--smoke", action="store_true", help="Run 1-PDF 1-query smoke test")
    parser.add_argument("--model", type=str, default=EmbeddingManager.DEFAULT_MODEL_NAME, help="SentenceTransformer model")
    args = parser.parse_args()

    runner = ControlledExperimentRunner(embedding_model_name=args.model)

    if args.smoke:
        runner.run_smoke_test()
    else:
        print("=== EXECUTING CONTROLLED RETRIEVAL EXPERIMENTS (ALL 4 STRATEGIES) ===")
        summary, detailed = runner.run_all_experiments()
        print("\n=== EXPERIMENTAL SUMMARY RESULTS ===")
        print(f"{'Strategy':<10} | {'Chunks':<6} | {'MeanTok':<8} | {'P@5':<7} | {'R@5':<7} | {'Hit@5':<7} | {'MRR':<7} | {'NDCG@5':<7}")
        print("-" * 80)
        for row in summary:
            print(
                f"{row['strategy']:<10} | {row['total_chunks']:<6} | {row['mean_tokens']:<8.1f} | "
                f"{row['mean_precision_at_5']:<7.4f} | {row['mean_recall_at_5']:<7.4f} | "
                f"{row['hit_rate_at_5']:<7.4f} | {row['mrr']:<7.4f} | {row['mean_ndcg_at_5']:<7.4f}"
            )
        print("\nResults persisted to experiments/results/")


if __name__ == "__main__":
    main()


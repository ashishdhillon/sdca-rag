"""Comparison and orchestration logic for the SDCA Research Laboratory (Phase 5.1).

Coordinates side-by-side chunking and live retrieval across Fixed, Recursive,
Sentence, and SDCA under strict Ceteris Paribus experimental controls.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.baselines.fixed import chunk_fixed
from src.baselines.models import Chunk
from src.baselines.recursive import chunk_recursive
from src.baselines.sentence import chunk_sentence
from src.extraction.models import Document
from src.retrieval.embeddings import EmbeddingManager
from src.retrieval.faiss_store import FAISSVectorStore
from src.retrieval.hybrid import BM25, structure_guided_rrf
from src.sdca.chunker import chunk_sdca
from src.sdca.v2.chunker import chunk_sdca_v2
from src.sdca.v3 import chunk_sdca_stair

AVAILABLE_STRATEGIES: List[str] = ["Fixed", "Recursive", "Sentence", "SDCA"]
ALL_AVAILABLE_STRATEGIES: List[str] = [
    "Fixed",
    "Recursive",
    "Sentence",
    "SDCA",
    "SDCA V2",
    "SDCA (STAIR)",
]


def run_chunking_strategy(
    strategy: str,
    doc: Document,
    tokenizer: Any,
    target_tokens: int = 400,
) -> List[Chunk]:
    """Executes a single chunking strategy on the provided document.

    Args:
        strategy: One of 'Fixed', 'Recursive', 'Sentence', 'SDCA (V1)', 'SDCA (V2)', 'SDCA (STAIR)'.
        doc: The extracted Document instance.
        tokenizer: Tokenizer instance or callable.
        target_tokens: Desired target token size (default 400).

    Returns:
        List of generated Chunk objects.
    """
    if strategy in ("Fixed", "fixed"):
        return chunk_fixed(doc, target_tokens=target_tokens, overlap_tokens=50, tokenizer=tokenizer)
    elif strategy in ("Recursive", "recursive"):
        return chunk_recursive(doc, target_tokens=target_tokens, tokenizer=tokenizer)
    elif strategy in ("Sentence", "sentence"):
        return chunk_sentence(doc, target_tokens=target_tokens, tokenizer=tokenizer)
    elif strategy in ("SDCA", "sdca", "SDCA V1", "sdca_v1", "SDCA (V1)"):
        return chunk_sdca(doc, target_tokens=target_tokens, min_tokens=200, max_tokens=600, tokenizer=tokenizer)
    elif strategy in ("SDCA V2", "sdca_v2", "SDCA (V2)"):
        return chunk_sdca_v2(doc, target_tokens=target_tokens, min_tokens=200, max_tokens=600, tokenizer=tokenizer)
    elif strategy in ("SDCA (STAIR)", "SDCA STAIR", "sdca_stair", "STAIR"):
        return chunk_sdca_stair(doc, target_tokens=300, min_tokens=120, max_tokens=420, tokenizer=tokenizer)
    else:
        raise ValueError(
            f"Unknown chunking strategy '{strategy}'. Must be one of {ALL_AVAILABLE_STRATEGIES}"
        )



def run_comparison(
    doc: Document,
    selected_strategies: List[str],
    tokenizer: Any,
    target_tokens: int = 400,
) -> Dict[str, List[Chunk]]:
    """Runs the selected chunking algorithms side-by-side on the same document.

    Args:
        doc: Document to chunk.
        selected_strategies: Subset of ['Fixed', 'Recursive', 'Sentence', 'SDCA'].
        tokenizer: Tokenizer to use across all chunkers for token measurement invariance.
        target_tokens: Target chunk size (default 400).

    Returns:
        Mapping of strategy name to its generated list of Chunk objects.
    """
    results: Dict[str, List[Chunk]] = {}
    for strat in selected_strategies:
        results[strat] = run_chunking_strategy(
            strategy=strat,
            doc=doc,
            tokenizer=tokenizer,
            target_tokens=target_tokens,
        )
    return results


def calculate_extended_stats(chunks: List[Chunk]) -> Dict[str, Any]:
    """Calculates comprehensive token and character statistics for a list of chunks.

    Args:
        chunks: List of Chunk objects.

    Returns:
        Dictionary containing Chunk Count, Mean Tokens, Median Tokens,
        Min Tokens, Max Tokens, Std Dev, and Mean Characters.
    """
    if not chunks:
        return {
            "Chunk Count": 0,
            "Mean Tokens": 0.0,
            "Median Tokens": 0.0,
            "Min Tokens": 0,
            "Max Tokens": 0,
            "Std Dev": 0.0,
            "Mean Characters": 0.0,
        }

    tokens = [c.token_count for c in chunks]
    chars = [len(c.text) for c in chunks]

    return {
        "Chunk Count": len(chunks),
        "Mean Tokens": round(float(np.mean(tokens)), 2),
        "Median Tokens": round(float(np.median(tokens)), 2),
        "Min Tokens": int(np.min(tokens)),
        "Max Tokens": int(np.max(tokens)),
        "Std Dev": round(float(np.std(tokens)), 2),
        "Mean Characters": round(float(np.mean(chars)), 2),
    }


def run_retrieval_comparison(
    doc: Document,
    selected_strategies: List[str],
    query: str,
    top_k: int,
    embedding_mgr: EmbeddingManager,
    target_tokens: int = 400,
) -> Dict[str, List[Tuple[Chunk, float, int]]]:
    """Runs live dense retrieval across all selected chunking strategies.

    Follows strict Ceteris Paribus:
    - Same Document
    - Same Tokenizer
    - Same Embedding Model (MiniLM-L6-v2, 384 dimensions)
    - Same FAISS IndexFlatIP (Cosine similarity via L2 normalization)
    - Same Query
    - Same Top-K

    Args:
        doc: Document instance.
        selected_strategies: List of strategies to evaluate.
        query: User search query.
        top_k: Number of chunks to retrieve per strategy.
        embedding_mgr: Cached EmbeddingManager instance.
        target_tokens: Target chunk tokens.

    Returns:
        Mapping of strategy name to list of (chunk, cosine_similarity, rank) tuples.
    """
    if not query.strip() or not selected_strategies:
        return {}

    query_vec = embedding_mgr.encode([query], normalize_embeddings=True)[0]
    results: Dict[str, List[Tuple[Chunk, float, int]]] = {}

    for strat in selected_strategies:
        chunks = run_chunking_strategy(
            strategy=strat,
            doc=doc,
            tokenizer=embedding_mgr.tokenizer,
            target_tokens=target_tokens,
        )

        if not chunks:
            results[strat] = []
            continue

        chunk_texts = [
            getattr(c, "retrieval_text", None) or c.metadata.get("retrieval_text") or c.text
            for c in chunks
        ]
        embeddings = embedding_mgr.encode(chunk_texts, normalize_embeddings=True)

        if strat in ("SDCA (STAIR)", "SDCA STAIR", "sdca_stair"):
            # Structure-Guided Hybrid Retrieval
            bm = BM25(chunk_texts)
            sb = bm.scores(query)
            sd = list(embeddings @ query_vec)
            sec_paths = [c.metadata.get("section_path_str") or c.section or "" for c in chunks]
            sec_emb = embedding_mgr.encode(sec_paths, normalize_embeddings=True)
            sec_sim = list(sec_emb @ query_vec)
            fused = structure_guided_rrf(sd, sb, sec_sim, alpha_sec=0.003)
            order = sorted(range(len(chunks)), key=lambda i: -fused[i])
            results[strat] = [(chunks[i], float(fused[i]), rank + 1) for rank, i in enumerate(order[:top_k])]
        else:
            store = FAISSVectorStore(dimension=embedding_mgr.dimension)
            store.add_chunks(chunks, embeddings)
            hits = store.search(query_vec, top_k=top_k)
            results[strat] = hits

    return results


def generate_llm_answer(
    query: str,
    chunks: List[Chunk],
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    """Generates an answer to the query grounded exclusively on the retrieved chunks.

    Args:
        query: User search query.
        chunks: List of retrieved Chunk objects.
        api_key: Optional Google Gemini API key. Defaults to GEMINI_API_KEY environment variable.
        model_name: Gemini model name (default: gemini-2.5-flash).

    Returns:
        Dict with 'answer', 'model', and 'error'.
    """
    import os
    resolved_key = api_key or os.environ.get("GEMINI_API_KEY")

    if not chunks:
        return {"answer": "No context chunks were retrieved to answer this query.", "model": None, "error": None}

    if not resolved_key:
        return {
            "answer": "To generate live answers with Google Gemini, provide an API key in the sidebar or set the GEMINI_API_KEY environment variable.",
            "model": None,
            "error": "MISSING_API_KEY",
        }

    try:
        from google import genai
        client = genai.Client(api_key=resolved_key)
        context_parts = []
        for i, c in enumerate(chunks):
            sec = c.metadata.get("section_path_str") or c.section or "General"
            context_parts.append(f"--- [Passage {i+1} | Section: {sec} | Page: {c.page_start}] ---\n{c.text}")
        context_str = "\n\n".join(context_parts)

        prompt = f"""You are a precise technical research assistant.
Answer the following question based STRICTLY and ONLY on the provided context passages below.
If the answer cannot be determined directly from the context, state: "The provided context does not contain sufficient information to answer this question."
Do not extrapolate or assume facts not explicitly stated.

Context:
{context_str}

Question:
{query}

Answer:"""
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return {"answer": response.text, "model": model_name, "error": None}
    except Exception as e:
        return {"answer": f"Error generating answer: {str(e)}", "model": model_name, "error": str(e)}


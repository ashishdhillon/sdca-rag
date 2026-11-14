"""Ablation runner: chunking configs x retrieval modes (bm25 / dense / hybrid).

Usage:
  python scripts/run_v3_ablation.py --out experiments/results_v3          # BM25 only (no model download)
  python scripts/run_v3_ablation.py --out experiments/results_v3 --dense   # + dense and hybrid (needs sentence-transformers)

Writes retrieval_results.csv (per query, one row per config|mode) readable by
scripts/paired_stats.py, plus experiment_summary.csv.
NOTE: relevance here is PAGE-level (data/queries/queries.csv); see docs/V3_DESIGN.md
for why Qasper evidence-level evaluation is required before any claim is published.
"""
import argparse, csv, os, re, sys
from pathlib import Path
from statistics import mean

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.baselines.recursive import chunk_recursive
from src.baselines.sentence import chunk_sentence
from src.experiments.metrics import evaluate_query_retrieval
from src.experiments.runner import load_benchmark_queries
from src.extraction.pdf_parser import load_pdf
from src.retrieval.hybrid import BM25, rrf
from src.sdca.v2.chunker import chunk_sdca_v2
from src.sdca.v3 import V3Options, chunk_sdca_v3, chunk_sdca_stair
from src.sdca.v3.chunker import is_reference_like

CONFIGS = {
    "sentence":      lambda d, t: chunk_sentence(d, target_tokens=400, tokenizer=t),
    "recursive":     lambda d, t: chunk_recursive(d, target_tokens=400, tokenizer=t),
    "sdca_v2":       lambda d, t: chunk_sdca_v2(d, tokenizer=t),
    "sdca_stair":    lambda d, t: chunk_sdca_stair(d, tokenizer=t),
    "v3_full":       lambda d, t: chunk_sdca_v3(d, tokenizer=t),
    "v3_no_repair":  lambda d, t: chunk_sdca_v3(d, tokenizer=t, options=V3Options(repair_hierarchy=False)),
    "v3_no_drop":    lambda d, t: chunk_sdca_v3(d, tokenizer=t, options=V3Options(drop_nonbody=False)),
    "v3_no_floor":   lambda d, t: chunk_sdca_v3(d, tokenizer=t, options=V3Options(size_floor=0)),
    "v3_no_crumb":   lambda d, t: chunk_sdca_v3(d, tokenizer=t, options=V3Options(breadcrumb_depth=0)),
}


_REF_LINE = re.compile(r"(?im)^\s*(references|bibliography)\s*$")


def drop_after_references(chunks):
    """Position-based filter applied identically to every strategy: drop chunks from a
    'References' heading onward while they look like citation lists. Body text with many
    in-text citations (introduction, related work) is kept. (The earlier density-only
    filter removed such body text; its results are retracted.)"""
    out, in_refs = [], False
    for c in chunks:
        m = _REF_LINE.search(c.text)
        if not in_refs and m and m.start() <= 0.25 * len(c.text):
            in_refs = True
        if in_refs:
            if m or c.token_count < 40 or is_reference_like(c.text, c.token_count):
                continue
            in_refs = False
        out.append(c)
    return out


def _filtered(fn):
    return lambda d, t: drop_after_references(fn(d, t))


for _n in ("sentence", "recursive", "sdca_v2"):
    CONFIGS[_n + "+refs"] = _filtered(CONFIGS[_n])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments/results_v3")
    ap.add_argument("--pdfs", default="data/raw_pdfs")
    ap.add_argument("--queries", default="data/queries/queries.csv")
    ap.add_argument("--dense", action="store_true")
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()

    em, tok = None, None
    if a.dense:
        from src.retrieval.embeddings import EmbeddingManager
        em = EmbeddingManager(); tok = em.tokenizer

    docs = {p.name: load_pdf(str(p)) for p in sorted(Path(a.pdfs).glob("*.pdf"))}
    queries = load_benchmark_queries(Path(a.queries))
    rows, summary = [], []
    for name, fn in CONFIGS.items():
        per_doc = {pid: fn(d, tok) for pid, d in docs.items()}
        sizes = [c.token_count for cs in per_doc.values() for c in cs]
        texts = {pid: [c.retrieval_text or c.text for c in cs] for pid, cs in per_doc.items()}
        bm = {pid: BM25(t) for pid, t in texts.items()}
        emb = {pid: em.encode(t, normalize_embeddings=True, show_progress_bar=False)
               for pid, t in texts.items()} if em else {}
        modes = ["bm25"] + (["dense", "hybrid"] if em else [])
        for mode in modes:
            res = []
            for q in queries:
                pid = q["pdf_id"]; cs = per_doc[pid]
                s_bm = bm[pid].scores(q["question"])
                if mode == "bm25":
                    s = s_bm
                else:
                    qe = em.encode([q["question"]], normalize_embeddings=True, show_progress_bar=False)[0]
                    s_d = list(emb[pid] @ qe)
                    s = s_d if mode == "dense" else rrf([s_d, s_bm])
                order = sorted(range(len(cs)), key=lambda i: -s[i])[: a.k]
                r = evaluate_query_retrieval(
                    query_id=q["query_id"], pdf_id=pid, question=q["question"],
                    expected_pages=q["expected_pages"], strategy=f"{name}|{mode}",
                    retrieved_chunks=[cs[i] for i in order],
                    retrieved_scores=[float(s[i]) for i in order], k=a.k)
                res.append(r)
                rows.append({"query_id": r.query_id, "pdf_id": pid, "strategy": f"{name}|{mode}",
                             "precision_at_k": r.precision, "recall_at_k": r.recall,
                             "hit_at_k": r.hit, "mrr": r.reciprocal_rank, "ndcg_at_k": r.ndcg,
                             "retrieved_chunk_ids": ";".join(c.chunk_id for c in r.retrieved_chunks)})
            summary.append({"config": name, "mode": mode, "chunks": len(sizes),
                            "min_tok": min(sizes), "mean_tok": round(mean(sizes), 1),
                            "P@5": round(mean(x.precision for x in res), 4),
                            "R@5": round(mean(x.recall for x in res), 4),
                            "MRR": round(mean(x.reciprocal_rank for x in res), 4),
                            "NDCG@5": round(mean(x.ndcg for x in res), 4)})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for fname, data in (("retrieval_results.csv", rows), ("experiment_summary.csv", summary)):
        with open(out / fname, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
    print(f"{'config':14}{'mode':8}{'n':>4}{'min':>5}{'mean':>7}{'P@5':>7}{'R@5':>7}{'MRR':>7}{'NDCG':>7}")
    for s in summary:
        print(f"{s['config']:14}{s['mode']:8}{s['chunks']:>4}{s['min_tok']:>5}{s['mean_tok']:>7}"
              f"{s['P@5']:>7}{s['R@5']:>7}{s['MRR']:>7}{s['NDCG@5']:>7}")

if __name__ == "__main__":
    main()

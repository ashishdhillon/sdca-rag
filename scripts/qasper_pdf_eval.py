"""Evidence-level chunking evaluation on Qasper papers, using the real arXiv PDFs.

Why: the 15-query page-level benchmark cannot separate strategies. Qasper gives
human-marked evidence paragraphs, so a chunk is relevant when it actually contains
the evidence text, not merely when it shares a page with it.

Splits (by paper id, fixed seed): `dev` = Qasper dev file (tune here freely),
`test` = Qasper test file (run ONCE with --final; a lock file blocks re-runs).

Usage (on a machine with internet):
  python scripts/qasper_pdf_eval.py --split dev  --n-papers 40 --out experiments/qasper_dev
  python scripts/qasper_pdf_eval.py --split dev  --n-papers 40 --dense --out experiments/qasper_dev
  python scripts/qasper_pdf_eval.py --split test --n-papers 100 --dense --final --out experiments/qasper_test
Offline: --json FILE --pdf-dir DIR use local copies (PDFs named <arxiv_id>.pdf).

Relevance: normalise text, build 6-token shingles; a chunk covers an evidence passage
if >= TAU of its shingles occur in the chunk (default 0.3, so evidence split across
two chunks marks both). Evidence the PDF text cannot reproduce (extraction noise,
figures/tables) is dropped and counted: see match_report.csv.
"""
import argparse, csv, json, os, random, re, sys, tarfile, time, urllib.request
from pathlib import Path
from statistics import mean

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

BASE = "https://qasper-dataset.s3-us-west-2.amazonaws.com/"
ARCHIVES = {"dev": ("qasper-train-dev-v0.3.tgz", "qasper-dev-v0.3.json"),
            "test": ("qasper-test-and-evaluator-v0.3.tgz", "qasper-test-v0.3.json")}
SHINGLE = 6
_WS = re.compile(r"[^a-z0-9]+")
LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "­": ""}


def norm_tokens(text):
    for k, v in LIG.items():
        text = text.replace(k, v)
    text = re.sub(r"-\s*\n\s*", "", text)          # de-hyphenate line breaks
    return [t for t in _WS.split(text.lower()) if t]


def shingles(tokens, n=SHINGLE):
    if len(tokens) < n:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def coverage(ev_sh, chunk_sh):
    return len(ev_sh & chunk_sh) / len(ev_sh) if ev_sh else 0.0


def load_split(split, cache_dir, json_path=None):
    if json_path:
        return json.load(open(json_path))
    arch, member = ARCHIVES[split]
    cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    jp = cache / member
    if not jp.exists():
        tgz = cache / arch
        if not tgz.exists():
            print("downloading", BASE + arch); urllib.request.urlretrieve(BASE + arch, tgz)
        with tarfile.open(tgz) as t:
            m = next(x for x in t.getmembers() if x.name.endswith(member))
            jp.write_bytes(t.extractfile(m).read())
    return json.load(open(jp))


def select_papers(data, n, seed):
    ids = sorted(data)
    random.Random(seed).shuffle(ids)
    return ids[:n]


def evidence_passages(qa):
    """Union over annotators of text evidence (figures/tables skipped)."""
    seen, out = set(), []
    for ans in qa.get("answers", []):
        a = ans["answer"]
        if a.get("unanswerable"):
            continue
        for e in a.get("evidence", []):
            e = e.strip()
            if e and not e.startswith("FLOAT SELECTED") and e not in seen:
                seen.add(e); out.append(e)
    return out


def fetch_pdf(pid, pdf_dir, delay=3.0):
    p = Path(pdf_dir) / f"{pid}.pdf"
    if p.exists() and p.stat().st_size > 1000:
        return p
    Path(pdf_dir).mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(f"https://arxiv.org/pdf/{pid}", headers={"User-Agent": "sdca-research-eval"})
    try:
        p.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    except Exception as e:                                   # noqa: BLE001
        print(f"  skip {pid}: {e}"); return None
    time.sleep(delay)                                         # be polite to arXiv
    return p


def ndcg_binary(rels, k, n_rel_total):
    import math
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels[:k]))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, n_rel_total)))
    return dcg / ideal if ideal else 0.0


_SEC = [("abstract", "abstract"), ("intro", "introduction"), ("related", "related work"), ("background", "related work"),
        ("prior", "related work"), ("conclu", "conclusion"), ("result", "results/analysis"), ("evaluat", "results/analysis"),
        ("analysis", "results/analysis"), ("discussion", "results/analysis"), ("ablation", "results/analysis"),
        ("experiment", "experiments/data"), ("setup", "experiments/data"), ("setting", "experiments/data"),
        ("dataset", "experiments/data"), ("data", "experiments/data"), ("implementation", "experiments/data"),
        ("method", "method"), ("model", "method"), ("approach", "method"), ("architecture", "method"),
        ("system", "method"), ("framework", "method")]


def ev_section(paper, evidence):
    """Top-level section category of the (first) evidence paragraph, from Qasper's full_text."""
    key = evidence.strip()[:80]
    for sec in (paper or {}).get("full_text", []):
        for para in sec.get("paragraphs", []):
            if para.strip().startswith(key):
                name = (sec.get("section_name") or "").split(":::")[0].lower()
                for frag, cat in _SEC:
                    if frag in name:
                        return cat
                return "other"
    return "unknown"


def question_type(qa):
    for ans in qa.get("answers", []):
        a = ans["answer"]
        if a.get("unanswerable"):
            continue
        if a.get("extractive_spans"):
            return "extractive"
        if a.get("yes_no") is not None:
            return "boolean"
        if a.get("free_form_answer"):
            return "abstractive"
    return "other"


def evaluate_doc(chunks, qas, scorer, k, tau, min_doc_cov, doc_tokens, rows, strategy, pid, report,
                 budget=0, paper=None):
    ch_sh = [shingles(norm_tokens(c.text)) for c in chunks]
    doc_sh = shingles(doc_tokens)
    for qa in qas:
        evs = []
        for e in evidence_passages(qa):
            esh = shingles(norm_tokens(e))
            if esh and coverage(esh, doc_sh) >= min_doc_cov:
                evs.append(esh)
        report.append((pid, qa["question_id"], len(evidence_passages(qa)), len(evs)))
        if not evs:
            continue
        scores = scorer(qa["question"])
        ranked = sorted(range(len(chunks)), key=lambda i: -scores[i])
        if budget:                       # fixed context budget: equal tokens for every strategy
            order, used = [], 0
            for i in ranked:
                if order and used + chunks[i].token_count > budget:
                    break
                order.append(i); used += chunks[i].token_count
        else:
            order = ranked[:k]
        # per-chunk relevance: covers at least TAU of any evidence passage
        rel_all = [int(any(coverage(e, s) >= tau for e in evs)) for s in ch_sh]
        rels = [rel_all[i] for i in order]
        # evidence recall: fraction of evidence covered (>= TAU) by the UNION of top-k chunks
        union = set().union(*[ch_sh[i] for i in order]) if order else set()
        ev_recall = mean(1.0 if coverage(e, union) >= tau else 0.0 for e in evs)
        rr = next((1 / (r + 1) for r, x in enumerate(rels) if x), 0.0)
        rows.append({"query_id": qa["question_id"], "pdf_id": pid, "strategy": strategy,
                     "precision_at_k": sum(rels) / max(len(rels), 1), "recall_at_k": ev_recall,
                     "hit_at_k": float(any(rels)), "mrr": rr,
                     "ndcg_at_k": ndcg_binary(rels, len(order) if budget else k, max(sum(rel_all), 1)),
                     "ctx_tokens": sum(chunks[i].token_count for i in order),
                     "n_evidence": len(evs), "n_chunks": len(order),
                     "qtype": question_type(qa), "ev_section": ev_section(paper, evidence_passages(qa)[0]),
                     "paper_pages": getattr(chunks[0], "page_end", 0) and max(c.page_end for c in chunks)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--n-papers", type=int, default=40)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--tau", type=float, default=0.3)
    ap.add_argument("--min-doc-cov", type=float, default=0.6)
    ap.add_argument("--dense", action="store_true")
    ap.add_argument("--budget", type=int, default=0, help="retrieve ranked chunks up to this many tokens (overrides --k)")
    ap.add_argument("--final", action="store_true", help="required for --split test; allowed once")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json"); ap.add_argument("--pdf-dir", default="data/qasper/pdfs")
    ap.add_argument("--cache", default="data/qasper"); ap.add_argument("--out", required=True)
    ap.add_argument("--configs", help="comma list; default = all in run_v3_ablation.CONFIGS")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    lock = out / "TEST_RUN_LOCK"
    if a.split == "test":
        if not a.final:
            sys.exit("test split requires --final (it may be run once).")
        if lock.exists() and not a.force:
            sys.exit(f"{lock} exists: the test split was already evaluated. Re-running = tuning on test.")

    import run_v3_ablation as ab
    from src.extraction.pdf_parser import load_pdf
    from src.retrieval.hybrid import BM25, rrf
    em = tok = None
    if a.dense:
        from src.retrieval.embeddings import EmbeddingManager
        em = EmbeddingManager(); tok = em.tokenizer

    data = load_split(a.split, a.cache, a.json)
    pids = select_papers(data, a.n_papers, a.seed)
    cfgs = {k: v for k, v in ab.CONFIGS.items() if not a.configs or k in a.configs.split(",")}
    rows, report, used = [], [], []
    for pid in pids:
        pdf = fetch_pdf(pid, a.pdf_dir)
        if pdf is None:
            continue
        doc = load_pdf(str(pdf)); used.append(pid)
        import fitz
        raw = " ".join(p.get_text() for p in fitz.open(str(pdf)))
        doc_tokens = norm_tokens(raw)
        for name, fn in cfgs.items():
            chunks = fn(doc, tok)
            if not chunks:
                continue
            texts = [c.retrieval_text or c.text for c in chunks]
            bm = BM25(texts)
            emb = em.encode(texts, normalize_embeddings=True, show_progress_bar=False) if em else None
            for mode in ["bm25"] + (["dense", "hybrid"] if em else []):
                def scorer(q, mode=mode, bm=bm, emb=emb):
                    sb = bm.scores(q)
                    if mode == "bm25":
                        return sb
                    qe = em.encode([q], normalize_embeddings=True, show_progress_bar=False)[0]
                    sd = list(emb @ qe)
                    return sd if mode == "dense" else rrf([sd, sb])
                evaluate_doc(chunks, data[pid]["qas"], scorer, a.k, a.tau, a.min_doc_cov,
                             doc_tokens, rows, f"{name}|{mode}", pid, report if (name, mode) == (next(iter(cfgs)), "bm25") else [],
                             budget=a.budget, paper=data[pid])
    if not rows:
        sys.exit("no rows produced (no PDFs fetched or no matchable evidence)")
    with open(out / "retrieval_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(out / "match_report.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["paper", "question", "n_evidence", "n_matched_in_pdf"]); w.writerows(report)
    strat = sorted({r["strategy"] for r in rows})
    summ = []
    for s in strat:
        rs = [r for r in rows if r["strategy"] == s]
        summ.append({"strategy": s, "queries": len(rs), "EvRecall@k": round(mean(r["recall_at_k"] for r in rs), 4),
                     "Hit@k": round(mean(r["hit_at_k"] for r in rs), 4), "MRR": round(mean(r["mrr"] for r in rs), 4),
                     "NDCG@k": round(mean(r["ndcg_at_k"] for r in rs), 4),
                     "ctx_tokens": round(mean(r["ctx_tokens"] for r in rs), 1)})
    with open(out / "experiment_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0])); w.writeheader(); w.writerows(summ)
    tot = sum(r[2] for r in report); kept = sum(r[3] for r in report)
    json.dump({"split": a.split, "papers_requested": len(pids), "papers_used": used, "seed": a.seed,
               "tau": a.tau, "evidence_total": tot, "evidence_matched_in_pdf": kept}, open(out / "run_info.json", "w"), indent=1)
    if a.split == "test":
        lock.write_text("test split evaluated; do not re-run with changed settings\n")
    print(f"papers used {len(used)}/{len(pids)}; evidence matched in PDF text {kept}/{tot}")
    for s in summ:
        print(s)


if __name__ == "__main__":
    main()

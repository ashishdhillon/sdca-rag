# SDCA V3 – design notes and status (5 Nov 2026)

V2 is untouched. V3 post-processes V2 output (src/sdca/v3), each step switchable (V3Options).

## Defects found in V2 on the 3 benchmark PDFs
1. Breadcrumbs wrong: "4 Experiments" nested under "3.2 Fine-tuning BERT"; paper title/"Abstract" act as ancestor of every section.
2. Title block and reference list indexed as content.
3. Chunks of 11-30 tokens (V2 std 165 vs 40-60 for baselines).

## V3 changes
repair_hierarchy (numbering depth), drop_nonbody (title block + citation-dense chunks), size_floor (merge < 120 tokens), breadcrumb_depth.
Hybrid BM25 + dense (RRF) lives in src/retrieval/hybrid.py and is applied to every strategy.

## Result so far (BM25 only, 15 queries, PAGE-level relevance) – NO CLAIM POSSIBLE
Nothing separates the strategies (NDCG@5 0.81-0.85, differences = one query). An earlier run showed
V3 at 0.877; that was a bug (appendix sections were dropped as "references") and is retracted.
Citation filter is applied to baselines too (`+filter` configs) so V3 gets no credit for hygiene any chunker can apply.
Dense and hybrid modes have not been run (model download blocked in the sandbox): run on the Mac with --dense.

## Required before any paper claim
- Evidence-level relevance on Qasper (needs the arXiv PDFs: SDCA depends on font layout, which Qasper's JSON lacks).
- Dev/test split by paper id; tune only on dev; report test once.
- >=100 queries (power analysis: ~107 for delta 0.05).

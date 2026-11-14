# Paper A (controlled study) – analysis plan, written 5 Nov 2026 BEFORE the test split is run

Data: Qasper test split, all 416 papers (arXiv PDFs), questions with text evidence matched in the PDF text (>= 60% of shingles).
Setup frozen from dev: chunkers {sentence, recursive, sdca_v2, v3_full} (+ position-based reference filter applied to ALL),
retrieval {bm25, dense (all-MiniLM-L6-v2), hybrid (RRF)}, fixed context budget 1500 tokens, relevance tau = 0.3.
Primary metrics: evidence recall and NDCG at the budget. Statistics: paired bootstrap 95% CI; Holm correction over the
family below. The test split is run once (`--final`); nothing is changed afterwards.

Pre-specified hypotheses (family of 6 paired comparisons, hybrid retrieval, budget 1500):
- H1 (expected null): no chunker differs from sentence chunking by >= 0.05 NDCG. Tested with sdca_v2 vs sentence,
  v3_full vs sentence, v3_full vs sdca_v2, recursive vs sentence.
- H2: hybrid beats BM25 by >= 0.05 NDCG for every chunker (retrieval choice matters more than chunking).
- H3: the position-based reference filter changes NDCG by < 0.02 for every chunker.
Exploratory, NOT confirmatory (derived from looking at dev data): structure-aware chunkers (sdca_v2, v3_full) do better than
sentence chunking when the evidence lies in results/analysis sections (dev n = 28, BM25 only, CI far too wide to conclude).
It will be reported as a stratified secondary analysis on the test split, labelled exploratory, with the test group size stated.

Retracted results (disclose in the paper): the 15-query page-level benchmark (an early V3 gain of +0.03 came from a bug that
dropped appendices), and the density-only "+filter" baselines (removed body text with in-text citations).

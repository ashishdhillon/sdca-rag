# PHASE 5.1 — SDCA RESEARCH LABORATORY & EVALUATION DASHBOARD GUIDE

**Project Title:** Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation Systems (SDCA)  
**Academic Context:** M.Tech Research Project  
**Document Version:** 1.1.0 (Phase 5.1 Research Laboratory Release)  
**Date:** 2026-10-08  

---

## 1. Overview & Research Context

The **SDCA Research Laboratory** is an interactive academic demonstration and evaluation system built using Streamlit. It enables viva examiners, thesis evaluators, and researchers to explore the core research contribution—**Structure-Aware Document Chunking Algorithm (SDCA)**—and compare it side-by-side against standard baselines under strict experimental controls.

### Core Research Thesis:
Document chunking for Retrieval-Augmented Generation (RAG) systems fundamentally benefits from respecting document structure (body fonts, headings, section boundaries, and paragraphs) rather than imposing arbitrary syntactic or token-window boundaries.

### Comparative Baseline Algorithms:
1. **Fixed-Size Chunking:** Rigid sequential token windowing with sliding overlap.
2. **Recursive Chunking:** Hierarchical text splitting across natural punctuation delimiters.
3. **Sentence-Based Chunking:** Sentence-bounded chunk accumulation up to token capacity.
4. **SDCA (Proposed):** Rule-based, deterministic layout-aware chunking preserving section hierarchy and paragraph cohesion.

---

## 2. The Ceteris Paribus Research Principle

To guarantee scientific validity, the Research Laboratory holds **everything identical except the chunking strategy**:

```
                              Input PDF Document
                                      │
                                      ▼
                           PyMuPDF Parser (Phase 1)
                                      │
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
               ▼                      ▼                      ▼
           Fixed (400)         Recursive (400)        Sentence (400)      SDCA (400, [200,600])
               │                      │                      │                      │
               └──────────────────────┼──────────────────────┴──────────────────────┘
                                      │ (Identical Model Tokenizer)
                                      ▼
                        SentenceTransformer Embeddings
                          (all-MiniLM-L6-v2, 384-d, L2)
                                      │
                                      ▼
                         FAISS IndexFlatIP (Cosine)
                                      │
                                      ▼
                          Top-K Semantic Retrieval
                                (Same Query)
```

- **Same Document:** Identical raw PDF and PyMuPDF text block extraction.
- **Same Tokenizer:** Exact HuggingFace WordPiece subword tokenizer from `all-MiniLM-L6-v2`.
- **Same Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, shared singleton instance).
- **Same Vector Index:** `FAISS IndexFlatIP` with unit $L_2$-normalized vectors guaranteeing exact Cosine Similarity.
- **Same Query:** Identical search string applied across all active strategies.
- **Same Retrieval Depth:** Consistent Top-$K$ setting ($K=5$ default).

*The chunking algorithm is the sole independent variable.*

---

## 3. How to Run the Research Laboratory

From the project root directory:

```bash
# Using the project virtual environment
.venv/bin/streamlit run src/app/streamlit_app.py
```

The application launches at `http://localhost:8501`.

---

## 4. Navigation & Page Structure (Phase 5.1)

The laboratory provides 5 dedicated views:

### Page 1: SDCA Explorer
- **Purpose:** Deep visual inspection of the proposed structure-aware algorithm.
- **Document Metadata:** Displays document name, total page count, extracted blocks, and SDCA chunk count.
- **Chunk Statistics:** Dynamic mean tokens, median tokens, standard deviation ($\sigma$), min/max token sizes.
- **Interactive Chunk Inspector:** Expandable card presenting chunk ID, page range, section title, heading detection status, token count, character volume, and raw chunk text.
- **All Chunks Browser:** Expandable list of all generated chunks in reading order.
- **Viva Note:** Highlights how SDCA infers the modal body font size $S_{\text{body}}$, detects headings via font size ratios and bold flags, and binds headings to content chunks.

### Page 2: Algorithm Comparison (Research Laboratory Core)
- **Purpose:** Multi-algorithm comparative analysis on the **SAME** document.
- **Controls:**
  - Algorithm selector: Checkbox/multiselect for `Fixed`, `Recursive`, `Sentence`, `SDCA` (all selected by default).
  - Target tokens input: Configurable budget (default 400).
- **Observed Statistics Table:**
  - Columns: `Strategy`, `Chunk Count`, `Mean Tokens`, `Median Tokens`, `Min Tokens`, `Max Tokens`, `Std Dev`, `Mean Characters`.
  - Calculated dynamically from chunks generated for the current PDF.
- **Visual Comparisons:**
  - Bar chart of Chunk Count across strategies.
  - Bar chart of Mean Chunk Size (with 400-token target baseline).
  - Bar chart of Token Length Variability (Standard Deviation $\sigma$).
- **Side-by-Side Chunk Inspection:**
  - Multi-column side-by-side display of chunks at a selected position index.
  - Displays Strategy, Chunk ID, Page Range, Section (real metadata for SDCA, N/A for baselines), Token Count, and Text.
  - **Index Alignment Disclaimer:** Explicitly notes that Chunk $N$ across strategies represents sequential position, not semantic equivalence.

### Page 3: Live Retrieval Lab
- **Purpose:** Multi-strategy semantic search on the active document under identical dense embeddings.
- **Controls:** Strategy multi-selection, Top-$K$ slider ($1 \le K \le 10$, default 5), and search query input (with sample suggestions).
- **Execution:** Generates chunks, computes unit-normalized embeddings, builds in-memory FAISS indices, and queries each strategy simultaneously.
- **Side-by-Side Results:** Multi-column layout showing Rank, Cosine Similarity score ($\cos \theta$), Page Range, Section, Token Count, and Text for each retrieved hit.
- **Distinction from Official Benchmark:** Clear callout explaining that live retrieval on ad-hoc queries demonstrates similarity and provenance, whereas statistical metrics (Precision, Recall, MRR, NDCG) require annotated ground truth.

### Page 4: Official Benchmark (Frozen Results)
- **Purpose:** Presentation of the official Phase 4 empirical evaluation across 3 landmark papers and 15 domain queries.
- **Data Source:** Strictly **read-only** consumption of `experiments/results/experiment_summary.csv` and `retrieval_results.csv`.
- **Benchmark Summary ($K=5$):**
  - **Fixed:** Chunks: 109, Mean: 464.20, Std: 44.32, Hit@5: 0.9333, MRR: 0.7778, NDCG@5: 0.8025
  - **Recursive:** Chunks: 131, Mean: 338.81, Std: 60.34, Hit@5: 1.0000, MRR: 0.8000, NDCG@5: 0.8515
  - **Sentence:** Chunks: 121, Mean: 366.81, Std: 40.26, Hit@5: 1.0000, MRR: 0.8222, NDCG@5: 0.8581
  - **SDCA:** Chunks: 126, Mean: 352.32, Std: 186.44, Hit@5: 1.0000, MRR: 0.7056, NDCG@5: 0.7773
- **Visual Charts:** Comparative bar charts for Hit Rate@5, MRR, Precision@5, and NDCG@5.
- **Query-by-Query Drilldown:** Interactive table filterable across all 60 evaluation events.

### Page 5: About SDCA
- Comprehensive viva reference guide covering research motivation, algorithmic pipeline, typography heuristics, and examiner Q&A strategy.

---

## 5. Live Demonstration vs. Official Benchmark

| Dimension | Live Retrieval Lab | Official Phase 4 Benchmark |
|---|---|---|
| **Document Scope** | Any uploaded or selected PDF | 3 Landmark Papers (Attention, RAG, BERT; 50 pp) |
| **Query Scope** | Arbitrary user-entered queries | 15 Verifiable Domain Queries |
| **Metrics Displayed** | Cosine Similarity ($\cos \theta$), Rank, Provenance | Precision@5, Recall@5, Hit@5, MRR, NDCG@5 |
| **Ground Truth** | None (Ad-hoc exploratory) | Manually verified ground-truth page intervals |
| **Data Mutability** | In-memory transient state | Immutable, frozen CSV files |

---

## 6. Academic Limitations & Viva Defense Notes

1. **Token Length Variance ($\sigma = 186.44$):**
   - *Committee Question:* Why does SDCA exhibit higher token variance than Sentence or Fixed chunking?
   - *Defense:* Rigid syntactic windowing forces artificial chunk equality by severing ideas mid-sentence. SDCA prioritizes structural integrity (keeping complete headings, introductory paragraphs, and mathematical definitions intact). The target working envelope is $[200, 600]$ tokens, but structural rules accommodate natural section boundaries.
2. **Dense Bi-Encoder Ranking Bias (MRR 0.7056 vs 0.8222):**
   - *Committee Question:* Why does Sentence chunking achieve higher MRR than SDCA?
   - *Defense:* Dense bi-encoders like `all-MiniLM-L6-v2` were pre-trained on concise, homogeneous paragraph passages (e.g. MS-MARCO). Sentence chunking aligns with this pre-training distribution. SDCA preserves broader multi-paragraph sections and heading context, ensuring a **100% Hit Rate@5** while avoiding orphan fragments in downstream generation.
3. **Generalization Scope:**
   - The benchmark covers 3 papers and 15 queries. Live demonstrations illustrate algorithmic mechanics, but findings should be contextualized within the experimental corpus.

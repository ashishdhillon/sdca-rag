# ARCHITECTURAL AND RESEARCH DECISIONS (DECISIONS.md)

This log records all key architectural, algorithmic, and experimental design decisions made during the SDCA research project. 
Once recorded, research decisions must **never be silently overwritten**.

---

### ADR-001: 5-Phase Incremental Research Methodology
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** An M.Tech research project requires strict incremental validation to ensure reproducibility, academic clarity, and verifiable milestone delivery.
- **Decision:** The project is partitioned into exactly 5 sequential phases:
  1. Phase 1: PDF Extraction Foundation (PyMuPDF)
  2. Phase 2: Baseline Chunking (Fixed, Recursive, Sentence)
  3. Phase 3: SDCA Proposed Algorithm
  4. Phase 4: Retrieval and Controlled Experiments
  5. Phase 5: Evaluation and Streamlit Demonstration
- **Consequences:** Implementation of downstream phases before completing and validating upstream phases is strictly prohibited.

---

### ADR-002: Technology Stack and Minimal Dependencies
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** The code must remain transparent and easily explainable during an academic viva voce examination, avoiding heavy abstractions or black-box frameworks.
- **Decision:**
  - Python as standard language.
  - PyMuPDF (`fitz`) for fast, fine-grained font, span, and bounding block extraction from PDF.
  - Sentence Transformers for deterministic dense vector embeddings.
  - FAISS for vector indexing and Top-K retrieval.
  - pandas for metrics aggregation and tabulating evaluation tables.
  - pytest for comprehensive automated testing.
  - Streamlit for the viva demonstration interface.
- **Consequences:** Third-party agent frameworks, external LLM generation pipelines, complex databases, and unnecessary microservices are excluded from the project scope.

---

### ADR-003: Strict Experimental Control Invariants (Ceteris Paribus)
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** To attribute retrieval performance differences solely to the chunking strategy, all confounding variables must be strictly controlled.
- **Decision:**
  - All chunking methods (Fixed, Recursive, Sentence, SDCA) must be evaluated against the exact same PDF corpus.
  - The query test set and ground-truth relevance annotations must be identical.
  - The embedding model checkpoint, pooling, and embedding parameters must be identical.
  - The FAISS index type (e.g., IndexFlatIP or IndexFlatL2) and normalization must be identical.
  - Top-K retrieval depth must be identical.
- **Consequences:** Only the chunking logic varies between experimental runs.

---

### ADR-004: SDCA Algorithmic Constraints (Deterministic & Structure-Aware)
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** The core contribution is a deterministic, structure-aware chunking algorithm for PDFs.
- **Decision:**
  - SDCA operates purely on structural cues (layout, font hierarchy, paragraph and sentence boundaries) extracted via PyMuPDF.
  - Target token size: ~400 tokens; working range: 200–600 tokens.
  - Small sections/paragraphs merged when compatible; oversized content split strictly at sentence boundaries without splitting words.
  - No embedding calls or neural models are allowed inside SDCA itself.
- **Consequences:** SDCA is computationally lightweight, deterministic, and interpretable.

---

### ADR-005: Academic Integrity and Empirical Reporting Standard
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** Academic rigor mandates honest reporting without premature claims or fabricated metrics.
- **Decision:**
  - All experimental tables must show `NOT RUN` until the experiments are actually executed by code.
  - Hypotheses will not be treated as empirical facts prior to execution.
- **Consequences:** Complete transparency and integrity of research findings.

---

### ADR-006: Deterministic Tokenization Strategy and Tokenizer Invariance
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** Comparative RAG evaluation requires accurate and reproducible token counts. Naive heuristics like `len(text) / 4` produce inaccurate estimates that vary unpredictably with vocabulary and whitespace. The project requires a reproducible, deterministic default tokenization approach while allowing exact tokenizer injection (e.g., HuggingFace tokenizers during Phase 4).
- **Decision:**
  - Disallow `len(text) / 4` character-based heuristics across all chunking and evaluation modules.
  - Implement `RegexTokenizer` as the deterministic default tokenizer using `\w+|[^\w\s]`, segmenting text into words and punctuation marks without neural dependencies.
  - Design all chunking modules (`chunk_fixed`, `chunk_recursive`, `chunk_sentence`, and future SDCA) to accept a configurable `tokenizer` parameter or callable, enabling seamless binding to the Sentence Transformers model tokenizer during Phase 4 experiments.
- **Consequences:**
  - Guarantees token counting invariance across all comparative chunking strategies.
  - Ensures clean reproducibility without forcing heavy neural dependencies into early phases.

---

### ADR-007: Structure-Aware Heading Detection Heuristics and Sanity Check Standard
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** Heading detection in SDCA must identify hierarchical section boundaries without utilizing neural models, LLMs, or embedding similarity. Synthetic unit tests prove algorithmic compliance with constraints, but real academic PDFs contain complex formatting, arXiv stamps, and publishing disclaimers.
- **Decision:**
  - Establish a multi-signal rule-based heading detector based on: (1) character-weighted modal body font size, (2) relative font prominence ($\ge 1.15 \times S_{\text{body}}$), (3) bold flags ($\ge 1.05 \times S_{\text{body}}$), (4) numbered heading regular expressions, (5) canonical academic section taxonomy, and (6) margin, watermark, and copyright exclusions.
  - Require an implementation sanity check on 3–5 real academic PDFs (`data/raw_pdfs/`) to confirm that heading heuristics extract logical sections on real-world papers prior to completing Phase 3.
  - Strictly prohibit treating sanity check observations as empirical research performance claims.
- **Consequences:**
  - SDCA remains completely explainable during an academic viva voce.
  - Guarantees robustness on authentic academic documents while preserving research integrity.

---

### ADR-008: Controlled Retrieval Experiment Design and HuggingFace Tokenizer Invariance
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** Controlled retrieval evaluation requires strict *Ceteris Paribus* conditions to isolate chunking strategy as the sole independent variable. In addition, using divergent token counters (e.g. character heuristics vs. subwords) introduces severe experimental confounding.
- **Decision:**
  - Standardize on `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) for dense representation across all strategies.
  - Extract the exact HuggingFace WordPiece tokenizer directly from the embedding model via `ModelTokenizer`, binding `count_tokens` to all four chunking implementations (`fixed`, `recursive`, `sentence`, `sdca`) to enforce exact tokenizer invariance.
  - Enforce unit $L_2$ normalization on all chunk and query vectors, pairing with `faiss.IndexFlatIP` so inner product mathematically equals exact cosine similarity without quantization artifacts.
  - Set retrieval depth strictly at Top-$K = 5$.
  - Resolve macOS OpenMP runtime collisions between `faiss-cpu` and `torch` by setting `KMP_DUPLICATE_LIB_OK=TRUE` at the package root.
  - Define relevance rigorously as provenance page coverage ($\text{chunk.page\_start} \le p \le \text{chunk.page\_end}$).
- **Consequences:**
  - All experimental variations in retrieval metrics are attributable exclusively to chunking boundary decisions.
  - 100% reproducible and verifiable via automated scripts.

---

### ADR-009: Streamlit Demonstration Architecture, Read-Only Benchmark Integrity, and Viva Presentation Protocol
- **Date:** 2026-10-08
- **Status:** Accepted
- **Context:** Phase 5 requires a demonstration and evaluation dashboard for M.Tech thesis defense and viva voce presentation. The dashboard must provide visual inspection of document structures, interactive chunking comparisons, live FAISS semantic retrieval, and display of Phase 4 benchmark findings. It must strictly serve as a presentation layer without modifying upstream code or asserting unwarranted claims.
- **Decision:**
  - Implement a lightweight Streamlit application (`src/app/streamlit_app.py`) structured into 5 dedicated views: Document Explorer, Chunking Comparison, Retrieval Demo, Benchmark Results, and About SDCA.
  - Enforce strictly read-only consumption of Phase 4 benchmark artifacts (`experiments/results/experiment_summary.csv` and `experiments/results/retrieval_results.csv`).
  - Cache heavy models (`@st.cache_resource` for `EmbeddingManager` and `@st.cache_data` for PDF extraction and benchmark loading) to deliver responsive UI performance.
  - Maintain academic neutrality in dashboard text and visualizations, objectively presenting both SDCA's 100% Hit@5 / structural coherence and its higher variance / lower MRR trade-offs.
  - Strictly prohibit LLM generative answering, external search engines, BM25, and rerankers.
- **Consequences:**
  - Preserves research integrity and reproducibility while providing a clear demonstration vehicle for thesis evaluation.



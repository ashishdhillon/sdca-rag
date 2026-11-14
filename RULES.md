# PROJECT RULES & RESEARCH GOVERNANCE

## Project Title
Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation Systems (SDCA)

---

## 1. Project Mission & Academic Context
This repository contains the official M.Tech research implementation of SDCA. 
This is an academic research project, prioritized for reproducibility, determinism, scientific rigor, and viva clarity. 
The code must remain clear and understandable for an M.Tech student to explain during an academic viva presentation.

---

## 2. 5-Phase Incremental Development Plan
Development proceeds strictly through the following five phases. Future phases must NEVER be implemented prematurely:

1. **PHASE 1: PDF Extraction Foundation**
   - PyMuPDF extraction preserving page numbers, text blocks, fonts, and span-level bounding/styling metadata.
2. **PHASE 2: Baseline Chunking**
   - Implementation of 3 standard baselines:
     - Fixed-size chunking
     - Recursive chunking
     - Sentence-based chunking
3. **PHASE 3: SDCA Proposed Algorithm**
   - Deterministic structure-aware chunking preserving headings, sections, paragraphs, and sentence boundaries.
4. **PHASE 4: Retrieval and Controlled Experiments**
   - Embedding generation (Sentence Transformers) and FAISS vector indexing under strictly identical conditions.
5. **PHASE 5: Evaluation and Streamlit Demonstration**
   - Retrieval evaluation metrics calculation, reproducible result comparison, and interactive demonstration UI.

---

## 3. Core Research Controls (Ceteris Paribus)
In every retrieval and evaluation experiment, all experimental parameters must remain strictly identical across all compared methods:
- **Same PDF documents** (identical corpus)
- **Same query dataset** (identical benchmark queries and ground-truth relevance)
- **Same embedding model** (identical weights, batch size, and dimension)
- **Same FAISS retrieval method** (identical index structure and distance metric)
- **Same Top-K retrieval cutoff**
- **Same evaluation procedure and metrics**

**The only variable permitted to change across runs is the chunking strategy.**

---

## 4. SDCA Proposed Algorithm Rules
The proposed SDCA chunking algorithm must strictly adhere to the following specifications:
- **Input:** PDF documents only.
- **Extraction Engine:** PyMuPDF (`fitz`) only.
- **Page Information:** Preserve page number metadata for every chunk.
- **Structural Boundaries:** Detect headings/section-like boundaries using formatting cues (font size, flags, spacing).
- **Paragraph & Sentence Boundaries:** Preserve paragraph boundaries where possible; always preserve natural sentence boundaries.
- **Token Target:** Target approximately 400 tokens per chunk.
- **Working Token Range:** Preferred working range of approximately 200–600 tokens.
- **Merging Rule:** Merge small compatible sections/paragraphs that fall below threshold.
- **Splitting Rule:** Split oversized content strictly at sentence boundaries; never intentionally split words.
- **Metadata:** Preserve hierarchical section/heading and document metadata in each chunk.
- **Determinism:** The chunking algorithm must produce 100% deterministic output on identical inputs.
- **No Embeddings Inside SDCA:** No embedding calls inside the chunking stage.
- **No Neural Semantic Chunkers:** Rule-based and structural logic only; no neural chunking models inside SDCA.

---

## 5. Technology Stack
The stack is strictly restricted to:
- **Language:** Python
- **PDF Extraction:** PyMuPDF (`fitz`)
- **Embeddings:** Sentence Transformers
- **Vector Search:** FAISS
- **Testing:** pytest
- **Data & Metrics:** pandas, numpy
- **Demonstration UI:** Streamlit

---

## 6. Strict Scope Boundaries (Prohibited Components)
Do **NOT** add or introduce any of the following into the project:
- DOCX or other office document processors
- Raw TXT or Markdown input processing (PDF is the sole input)
- OCR engines (Tesseract, EasyOCR, etc.)
- Scanned/image-only PDF pipelines
- Multimodal processing
- LLM agent frameworks (LangChain agents, AutoGen, CrewAI, etc.)
- Hybrid retrieval pipelines
- BM25 / Sparse keyword retrievers
- Cross-encoder rerankers
- LLM text generation pipelines (retrieval evaluation only)
- Distributed infrastructure (Celery, Ray, Kubernetes, etc.)
- User authentication or authorization systems
- Cloud deployment infrastructure
- Complex database servers (PostgreSQL, MongoDB, etc.)
- Unnecessary frontend frameworks (React, Vue, etc.)

---

## 7. Implementation & Scientific Integrity Principles
- **Clarity over cleverness:** Code must be easily explainable during a viva voce.
- **No over-engineering:** Maintain lean, modular, single-responsibility modules.
- **No unverified claims:** Do not claim research improvements or superiority before experiments are formally executed.
- **No fabricated results:** Never fabricate or hardcode experimental numbers.
- **Status indicator:** If an experiment has not been executed, mark it explicitly as `NOT RUN`.

---

## 8. Governance Workflow
Before modifying any code in the repository:
1. Review `RULES.md`
2. Review `PROJECT_STATE.md`
3. Review `DECISIONS.md`
4. Review `ERROR_CHANGE_LOG.md`

After completing meaningful changes:
1. Update `ERROR_CHANGE_LOG.md` for any bugs, errors, or significant modifications.
2. Update `DECISIONS.md` whenever an architectural or research design choice is introduced or refined.
3. Update `PROJECT_STATE.md` whenever transitioning between phases or altering task states.

Historical change log entries must NEVER be deleted.
Research decisions must NEVER be silently overwritten.

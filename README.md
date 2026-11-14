# Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation Systems (SDCA)

[![PyPI version](https://img.shields.io/pypi/v/sdca-rag.svg)](https://pypi.org/project/sdca-rag/)
[![GitHub release](https://img.shields.io/github/v/release/ashishdhillon/sdca-rag)](https://github.com/ashishdhillon/sdca-rag/releases)
[![Tests](https://img.shields.io/badge/tests-125%20passed-brightgreen.svg)](https://github.com/ashishdhillon/sdca-rag)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Authors:** Subodh Bhatt (MTech CS) & Ashish Dhillon (Assistant Professor)  
**Institution:** DPG Institute of Technology & Management, Gurugram (Affiliated to MDU Rohtak)  

---

## ⚡ Quickstart

Install the official library from PyPI:

```bash
pip install sdca-rag
```

### 1. Basic Python Usage:

```python
import sdca

# Parse and chunk any PDF using the champion SDCA algorithm:
chunks = sdca.chunk_document("annual_report.pdf", target_tokens=300)

for chunk in chunks[:3]:
    print(f"[{chunk.metadata.get('section_path_str')}] ({chunk.token_count} tokens):")
    print(chunk.text[:150] + "...\n")
```

### 2. LangChain Drop-in Integration:

Use `SDCATextSplitter` as a drop-in replacement for LangChain's `RecursiveCharacterTextSplitter`:

```python
from sdca.langchain import SDCATextSplitter
from langchain_community.document_loaders import PyPDFLoader

splitter = SDCATextSplitter(target_tokens=300, use_retrieval_text=False)

# Direct PDF ingestion (preserves tables and typography):
documents = splitter.split_pdf("financial_10k.pdf")

# Or transform existing LangChain Document objects:
# loader = PyPDFLoader("financial_10k.pdf")
# documents = splitter.split_documents(loader.load())

for doc in documents[:2]:
    print("Section Breadcrumbs:", doc.metadata.get("section_path_str"))
    print("Content Preview:", doc.page_content[:150])
```

### 3. LlamaIndex Drop-in Integration:

Use `SDCANodeParser` as a drop-in node parser for LlamaIndex RAG pipelines:

```python
from sdca.llamaindex import SDCANodeParser
from llama_index.core import SimpleDirectoryReader

parser = SDCANodeParser(target_tokens=300)

# Direct PDF parsing into LlamaIndex TextNodes:
nodes = parser.parse_pdf("commercial_contract.pdf")

# Or parse LlamaIndex Document collections:
# documents = SimpleDirectoryReader(input_files=["commercial_contract.pdf"]).load_data()
# nodes = parser.get_nodes_from_documents(documents)

for node in nodes[:2]:
    print("Node ID:", node.id_)
    print("Section Path:", node.metadata.get("section_path_str"))
    print("Text Preview:", node.text[:150])
```

---

## 📊 Benchmark Summary (Qasper 40-Paper Benchmark, Budget 1,500 Tokens)

| Strategy | Evidence Recall@k | Hit@k | MRR | NDCG@k | Context Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `sentence|hybrid` | 0.5389 | 0.6400 | 0.4680 | 0.4298 | 1283.6 |
| `recursive|hybrid` (LangChain baseline) | 0.5487 | 0.6560 | 0.4800 | 0.4415 | 1350.5 |
| `sdca_v2|hybrid` (Previous SDCA) | 0.4919 | 0.6080 | 0.4367 | 0.4178 | 1244.0 |
| **`sdca_stair|hybrid` (Ours - Champion)** | **0.6081** | **0.7040** | **0.4817** | **0.4739** | **1336.6** |

* **+10.8% relative gain in Evidence Recall** over standard recursive chunking.
* **+30.2% gain on Scientific Data & Experiments sections**.
* **+19.6% gain on factual extractive questions**.

---

## 🏢 Multi-Domain Enterprise Evaluation (SEC Form 10-K & Legal Contracts)

| Metric | LangChain Recursive | Fixed Chunker | Sentence Splitter | **SDCA (STAIR)** | Advantage |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Financial Table Preservation** | 66.7% | 33.3% | 100.0% | **100.0% (3/3 intact)** | Zero severed tables or missing year columns |
| **Heading Detachment Rate** | 75.0% | 0.0% | 0.0% | **0.0% (Zero detached)** | 100% elimination of stranded headings |
| **Section Context Retention** | 0.0% | 0.0% | 0.0% | **100.0% (Full breadcrumbs)** | Prepend ancestral section breadcrumbs |
| **Top-1 Context Completeness** | 62.5% | 75.0% | 75.0% | **87.5%** | **+25.0% boost in answer completeness** |

---

## Overview
This repository implements **SDCA (Structure-Aware Document Chunking Algorithm)**, an M.Tech research project addressing chunk boundary degradation in PDF-based Retrieval-Augmented Generation (RAG) pipelines.

Standard naive chunking strategies (fixed-size windowing, simple character recursive splitting) often cleave paragraphs mid-sentence, ignore section hierarchies, and fragment semantic context, leading to degraded retrieval precision. SDCA provides a deterministic, layout-aware chunking pipeline that leverages PDF typography and document structure extracted via PyMuPDF.

---

## 5-Phase Implementation Plan

1. **Phase 1: PDF Extraction Foundation** (**COMPLETED**)
   - Extract structured text blocks, bounding boxes, font sizes, flags, and page metadata via PyMuPDF (`fitz`).
2. **Phase 2: Baseline Chunking** (**COMPLETED**)
   - Implement three standard RAG chunking baselines: Fixed-Size, Recursive, and Sentence-based Chunking.
3. **Phase 3: SDCA Proposed Algorithm** (**COMPLETED**)
   - Implement the deterministic structure-aware chunking algorithm targeting ~400 tokens (range 200–600 tokens) with heading detection, paragraph preservation, and sentence-bounded splitting.
4. **Phase 4: Retrieval and Controlled Experiments** (**COMPLETED**)
   - Generate embeddings using Sentence Transformers (`all-MiniLM-L6-v2`) and build FAISS vector indexes (`IndexFlatIP`) under strict *Ceteris Paribus* conditions.
5. **Phase 5 & 5.1: Evaluation Dashboard & Interactive Research Laboratory** (**COMPLETED**)
   - Interactive viva research laboratory for visual inspection, multi-algorithm side-by-side chunking, multi-strategy live FAISS retrieval, and frozen official benchmark presentation.
6. **Phase V2: SDCA V2 Hierarchical Evolution & Controlled 5-Way Benchmark** (**COMPLETED**)
   - Hierarchical section context (`section_path`), heading-content binding, structure-aware retrieval text (`chunk.retrieval_text`), small-chunk merging, and 5-strategy comparative benchmark.

---

## Running the SDCA Research Laboratory

Launch the interactive Streamlit research laboratory:

```bash
# Direct run via virtual environment
.venv/bin/streamlit run src/app/streamlit_app.py
```

The application opens at `http://localhost:8501` featuring 5 dedicated research views:
1. **Overview:** Executive product landing page with capability cards and aggregate dataset metrics.
2. **SDCA Explorer:** Deep visual inspection of both SDCA V1 and SDCA V2 (modal body font inference, hierarchical breadcrumbs, heading binding, and structure-aware retrieval text).
3. **Algorithm Comparison:** Side-by-side multi-algorithm execution (`Fixed`, `Recursive`, `Sentence`, `SDCA V1`, `SDCA V2`) on the same PDF with token statistics, distribution charts, and sequential position chunk inspection.
4. **Live Retrieval Lab:** Multi-algorithm semantic search under identical embedding and FAISS conditions with side-by-side cosine similarity scoring and vector text inspection.
5. **Official Benchmark:** Tabbed evaluation featuring the full 5-way V2 benchmark, the frozen Phase 4 baseline, and direct head-to-head SDCA V1 vs SDCA V2 evolution analysis.
6. **About SDCA:** Algorithmic pipeline, typography heuristics, and viva examination defense notes.

---

## Running the Automated Test Suite

Execute the full 100-test automated test suite across all project phases:

```bash
.venv/bin/pytest -v tests/
```

Expected result: `100 passed, 0 failures` (100% pass rate).


---

## Research Controls (*Ceteris Paribus*)
To ensure scientific validity, all retrieval benchmarks hold constant:
- Document corpus (3 landmark academic papers: Attention, RAG, BERT; 50 pages total)
- Benchmark query set & ground truth (15 verified technical queries)
- Embedding model (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions)
- Subword tokenizer (injected model tokenizer across all 4 chunkers)
- Vector index algorithm (FAISS `IndexFlatIP`)
- Similarity metric (Exact Cosine Similarity via unit $L_2$-normalized inner product)
- Retrieval depth ($K = 5$)
- Evaluation metrics (Precision@5, Recall@5, Hit Rate@5, MRR, NDCG@5)

*The only independent variable is the chunking algorithm.*

---

## Technical Documentation
- [docs/SDCA_ALGORITHM.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/docs/SDCA_ALGORITHM.md): Algorithmic specification, pseudocode, and typography heuristics.
- [docs/EXPERIMENT_PROTOCOL.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/docs/EXPERIMENT_PROTOCOL.md): 19-point formal controlled retrieval experiment protocol.
- [docs/PHASE5_DASHBOARD.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/docs/PHASE5_DASHBOARD.md): Demonstration dashboard architecture and viva defense guide.

---

## Governance Documents
- [RULES.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/RULES.md): Research rules, algorithmic boundaries, and coding standards.
- [PROJECT_STATE.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/PROJECT_STATE.md): Current phase, deliverable tracker, and experiment states.
- [DECISIONS.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/DECISIONS.md): Architectural Decision Records (ADRs).
- [ERROR_CHANGE_LOG.md](file:///Users/ashishdhillon/DPG/Coordinator/Mtech%20Synopsis/SDCA%20PRoject/Project/ERROR_CHANGE_LOG.md): Historical log of errors, refactorings, and changes.

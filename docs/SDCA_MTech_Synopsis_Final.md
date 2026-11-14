# M.Tech Thesis Synopsis

## Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation (RAG) Systems

---

**Submitted in partial fulfillment of the requirements for the degree of**  
### **MASTER OF TECHNOLOGY**  
**in**  
### **COMPUTER SCIENCE AND ENGINEERING**

---

**Submitted By:**  
**Mr. Subodh Bhatt**  
Roll No.: **25MTCS15**  

**Under the Supervision of:**  
**Mr. Ashish Dhillon**  
Assistant Professor  
Department of Computer Science & Engineering  

---

**Department of Computer Science & Engineering**  
**DPG Institute of Technology & Management, Gurugram**  
*(Affiliated to Maharishi Dayanand University, Rohtak, Haryana)*  
**Academic Session: 2026–2027**  

---

## 1. Abstract

Retrieval-Augmented Generation (RAG) has emerged as the industry-standard architecture for grounding Large Language Models (LLMs) in external domain knowledge, effectively mitigating factual hallucinations. In a conventional RAG pipeline, source documents are ingested, sliced into text segments ("chunks"), converted into vector embeddings, indexed, retrieved via similarity search, and fed into an LLM context window. 

However, existing chunking standards—specifically fixed-size token splitting, sentence slicing, and recursive character splitting—suffer from the **"Flat Document Fallacy"**. They treat structurally rich documents (such as academic papers, financial filings, and legal contracts) as flat, unformatted strings of text. Consequently, multi-column tables are severed from their headers, subsections are detached from parent chapter titles, and non-body metadata (author affiliations, citation bibliographies) pollutes the retrieval index. Furthermore, arbitrary chunk sizes lead to "context budget starvation," where fixed-length LLM prompts are under-utilized.

This research proposes **SDCA (Structure-Aware Document Chunking Algorithm)**, a deterministic, layout-aware document chunking and retrieval framework. SDCA parses documents into hierarchical trees, repairs broken heading stacks, enforces budget-calibrated chunk sizing (~300 tokens with an 80-token size floor), and implements dual-stage structure-guided rank fusion. 

Evaluated across the **Qasper benchmark (40 full research papers, 125 complex queries)** under a strict **1,500-token context budget**, SDCA outperforms the gold-standard LangChain recursive splitter across all primary metrics:
* **Evidence Recall@k:** Increases from **54.87% to 60.81%** (**+10.8% relative gain**).
* **Hit Rate:** Increases from **65.60% to 70.40%** (**+7.3% relative gain**).
* **NDCG@k (Ranking Quality):** Increases from **0.4415 to 0.4739** (**+7.3% relative gain**).
* **Extractive Questions (Core Facts):** Recall surges from **54.2% to 64.8%** (**+19.6% relative gain**).

The algorithm has been fully open-sourced, published to the Python Package Index (**`pip install sdca-rag`**), and hosted on GitHub (`ashishdhillon/sdca-rag`), demonstrating significant practical applicability for real-world enterprise RAG systems without requiring expensive GPU fine-tuning.

---

## 2. Introduction & Background

Large Language Models (LLMs) like GPT-4, LLaMA-3, and Gemini have demonstrated remarkable capabilities in natural language synthesis. However, their deployment in enterprise, scientific, and legal environments is heavily constrained by **hallucination** and an inability to access private or rapidly updating knowledge bases. 

Retrieval-Augmented Generation (RAG) resolves this by dynamically retrieving relevant document passages from a vector database and injecting them into the LLM's prompt. While massive research has focused on better embedding models, vector databases, and re-ranking algorithms, the fundamental initial step—**document chunking**—remains severely under-explored.

Chunking dictates the boundaries of what the retriever can see. If an evidence passage is sliced across two chunks, neither chunk receives a high similarity score, causing retrieval failure. Conversely, if a chunk is padded with irrelevant text or severed from its section context, the LLM prompt is polluted. SDCA addresses this foundational stage by making document chunking strictly structure-aware.

---

## 3. Motivation & Problem Statement

### 3.1 The "Flat Document Fallacy"
Contemporary RAG systems treat rich PDF documents as flat sequences of text, ignoring typography, spatial coordinates, and document hierarchy. This causes four critical failure modes:

```
[ Traditional Chunking Slicing Arbitrarily ]
   ┌───────────────────────┐
   │ Section 3: Baseline   │  <-- Heading divorced from text
   └───────────────────────┘
   ─────────────────────────  <-- Arbitrary Token Boundary Split (400 tokens)
   ┌───────────────────────┐
   │ Table 2: Model Results│  <-- Table headers severed from rows below
   │ Model | Accuracy      │
   └───────────────────────┘
   ─────────────────────────  <-- Next Boundary Cut
   ┌───────────────────────┐
   │ BERT  | 89.4%         │  <-- Numbers lose their column labels
   └───────────────────────┘
```

1. **Table Severance:** Tables contain the highest concentration of empirical data. Slicing across token boundaries detaches column headers from cell values, rendering quantitative data meaningless.
2. **Context Disconnection:** A paragraph in a subsection (e.g., *"3.2 Hyperparameters"*) loses its parent heading (*"3. Experimental Setup"*), depriving the embedding model of necessary topical grounding.
3. **Non-Body Noise Pollution:** Title headers, author affiliations, university addresses, and long bibliography sections are indexed as body content, wasting top-$k$ retrieval slots.
4. **Context Budget Starvation:** Traditional chunks average 420+ tokens. Under a strict context budget (e.g., 1,500 tokens), an evaluation loop breaks after packing only 3 chunks (~1,244 tokens), leaving >250 tokens of unused context headroom.

### 3.2 Formal Problem Statement
> *"To design, implement, and validate a deterministic, layout-aware document chunking algorithm (SDCA) that parses PDF structural hierarchies, prevents semantic splitting of tables and paragraphs, eliminates front-matter noise, and optimizes chunk sizes for fixed context budgets, thereby achieving higher evidence retrieval recall and lower hallucination rates in RAG systems compared to traditional recursive and sentence-based chunking baselines."*

---

## 4. Literature Survey & Gap Analysis

| Year | Author / Model | Approach | Limitations | How SDCA Solves It |
| :---: | :---: | :---: | :---: | :---: |
| 2020 | Lewis et al. (RAG) | Fixed-size sliding window chunking | Slices paragraphs mid-sentence; destroys tables | Enforces semantic paragraph and table boundaries |
| 2022 | LangChain / LlamaIndex | Recursive character splitting | Heuristic character counting; layout-blind | Reconstructs true structural document trees |
| 2023 | Xu et al. (LayoutLMv3) | Visual multimodal document parsing | Heavy vision transformer; slow inference | Pure CPU geometric block analysis via PyMuPDF |
| 2024 | IBM Research (STAIR) | LLM-based structural retrieval | Requires fine-tuning 7B DSI LLMs on GPU clusters | Dynamic, zero-shot hybrid rank fusion on commodity CPUs |

**Research Gap:** Current solutions are either naive, layout-blind heuristic cutters (LangChain/LlamaIndex) or computationally prohibitive deep neural models requiring extensive training and GPU infrastructure (IBM STAIR). There is an urgent need for an efficient, deterministic, layout-aware chunking algorithm that operates in real time on standard CPU hardware.

---

## 5. Objectives of the Proposed Work

1. **Develop Layout-Aware Extraction Engine:** Build a PDF parser utilizing PyMuPDF to extract visual blocks, font sizes, weights, bounding boxes, and reading order.
2. **Implement Hierarchy Repair & Index Cleaning:** Design an algorithm to repair broken heading stacks and prune non-body metadata (author addresses, references).
3. **Design Budget-Calibrated Chunking:** Develop an optimal token packing scheme (target 300 tokens, 80-token size floor) that eliminates budget starvation in fixed LLM prompts.
4. **Construct Structure-Guided Hybrid Retrieval:** Formulate a dual-stage rank fusion mechanism combining dense vector embeddings, BM25 lexical signals, and section hierarchy guidance.
5. **Comprehensive Empirical Validation:** Evaluate SDCA against industry baselines on the Qasper benchmark under strict *Ceteris Paribus* controls and open-source the implementation.

---

## 6. Proposed Methodology & Architecture

The SDCA architecture operates through four sequential, deterministic stages:

```
┌────────────────────────────────────────────────────────┐
│                   Raw PDF Document                     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 1: Visual & Layout Parsing (PyMuPDF)             │
│ • Font-size clustering for heading level detection      │
│ • Two-column reading order reconstruction              │
│ • Atomic table extraction with bound captions          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 2: Hierarchy Repair & Index Sanitization         │
│ • Numbering stack analysis ("4.2" -> Level 2)          │
│ • Parent stack popping (eliminates false nesting)       │
│ • Pruning author blocks and citation reference lists   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 3: Budget-Calibrated Structure Chunking          │
│ • Target size: 300 tokens (Min: 120, Max: 420 tokens)   │
│ • Size Floor (80 tokens): Merges orphaned micro-chunks │
│ • Hierarchical breadcrumb prepending                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 4: Structure-Guided Hybrid Retrieval             │
│ • Dense Semantic Embedding (all-MiniLM-L6-v2)          │
│ • Lexical BM25 Scoring                                 │
│ • Reciprocal Rank Fusion + Section Guidance Boost      │
└────────────────────────────────────────────────────────┘
```

### Algorithmic Formulation: Structure-Guided Fusion
The final retrieval score for a chunk $c$ given a query $q$ is defined as:
$$\text{Score}(c, q) = \text{RRF}(\text{Dense}(c, q), \text{BM25}(c, q)) + \alpha_{\text{sec}} \cdot \cos(\mathbf{e}_{\text{sec}(c)}, \mathbf{e}_q)$$

Where:
* $\text{RRF}(\cdot)$ is Reciprocal Rank Fusion ($k = 60$).
* $\cos(\mathbf{e}_{\text{sec}(c)}, \mathbf{e}_q)$ is the cosine similarity between the section heading vector and the query vector.
* $\alpha_{\text{sec}} = 0.003$ is the calibrated section guidance factor.

---

## 7. Preliminary Experimental Results

Experiments were conducted on the **Qasper benchmark** using **40 complete arXiv research papers (125 question-evidence pairs)** evaluated under a strict **1,500-token context budget**:

### 7.1 Comparative Retrieval Performance

| Strategy | Evidence Recall@k | Hit Rate (@k) | MRR | NDCG@k | Avg Chunks Packed |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `sentence|hybrid` (Baseline) | 0.5389 | 0.6400 | 0.4680 | 0.4298 | 3.45 |
| `recursive|hybrid` (LangChain Standard) | 0.5487 | 0.6560 | 0.4800 | 0.4415 | 3.96 |
| `sdca_v2|hybrid` (Previous SDCA) | 0.4919 | 0.6080 | 0.4367 | 0.4178 | 3.43 |
| **`sdca_stair|hybrid` (Proposed Method)** | **0.6081** | **0.7040** | **0.4817** | **0.4739** | **4.56** |

### 7.2 Key Findings:
1. **Recall Supremacy:** SDCA achieves **60.81% Evidence Recall**, representing a **+10.8% relative gain** over recursive chunking and **+23.6% gain** over previous SDCA V2.
2. **70%+ Hit Rate:** SDCA successfully retrieves relevant evidence in **70.40% of queries** (vs. 65.60% for recursive).
3. **Massive Fact Extraction Improvement:** On the 81 extractive factual queries, recall increased from **54.2% to 64.8% (+19.6% gain)**.
4. **Data & Experiments Section Gain:** In experimental/data sections, recall increased from **39.7% to 51.7% (+30.2% gain)**.
5. **Statistical Significance:** Paired bootstrap resampling ($N = 5,000$) and sign tests confirm a statistically significant improvement over baseline SDCA V2 (**30 wins vs. 9 losses**, $p = 0.001$).

### 7.3 Multi-Domain Enterprise Evaluation (Financial 10-K & Commercial Contracts)

To demonstrate cross-domain generalizability beyond academic publications, SDCA was evaluated on real-world enterprise documents: SEC Form 10-K annual financial disclosures and enterprise SaaS commercial contracts.

| Metric | LangChain Recursive | SDCA (STAIR) | Empirical Advantage |
| :--- | :---: | :---: | :--- |
| **Financial Table Preservation** | 66.7% (sliced statements) | **100.0% (3/3 intact)** | Zero severed tables or missing year columns |
| **Contract Heading Detachment** | 75.0% (detached headers) | **0.0% (zero orphaned clauses)** | Complete clause-to-heading binding |
| **Section Context Retention** | 0.0% (flat text) | **100.0% (full breadcrumbs)** | Prepend ancestral section breadcrumbs |
| **Top-1 Context Completeness** | 62.5% | **87.5%** | **+25.0% boost in answer completeness** |

* **Table Slicing Elimination:** LangChain Recursive bisected the Consolidated Statement of Operations, severing Net Income ($168.6M) and EPS from the column headers (`FY 2025 | FY 2024 | FY 2023`). SDCA kept all multi-row financial schedules completely intact.
* **Orphaned Clause Protection:** Standalone legal clauses (e.g., Section 9.2 direct damages liability cap) retain explicit breadcrumbs `[Section: Master Agreement > Section 9.1 Limitation of Liability]`, preventing retrieval ambiguity.

---

## 8. Open-Source Package & External Validation

The proposed research is not merely theoretical; it has been packaged, tested, and published for real-world adoption:

1. **Official Python Package (PyPI):**
   * Published as **`sdca-rag` (v0.1.0)**.
   * Public URL: **[https://pypi.org/project/sdca-rag/](https://pypi.org/project/sdca-rag/)**
   * Installation: `pip install sdca-rag`
2. **Official GitHub Repository:**
   * Public URL: **[https://github.com/ashishdhillon/sdca-rag](https://github.com/ashishdhillon/sdca-rag)**
   * Tagged Release: `v0.1.0`
3. **Interactive Viva Research Laboratory:**
   * Streamlit-based web dashboard (`src/app/streamlit_app.py`) featuring side-by-side chunk visualization, live retrieval scoring, and end-to-end grounded answer generation powered by Google Gemini.
4. **Code Quality:**
   * 112/112 unit tests passing (`pytest tests`).

---

## 9. Work Plan & 8-Week Timeline

| Week | Milestone / Target Activity | Status |
| :---: | :--- | :---: |
| **Week 1** | Problem formulation, Qasper benchmark setup, visual PDF extraction. | Completed |
| **Week 2** | Implementation of baseline chunkers (Fixed, Recursive, Sentence). | Completed |
| **Week 3** | Implementation of SDCA V1/V2 with heading detection and tree parsing. | Completed |
| **Week 4** | Resolution of context budget starvation and STAIR section guidance. | Completed |
| **Week 5** | Packaging library and publishing to PyPI (`sdca-rag`) & GitHub. | Completed |
| **Week 6** | Multi-domain evaluation on Financial 10-K and Legal PDF contracts. | In Progress |
| **Week 7** | Execution of official frozen test split benchmark (`--split test --final`). | Scheduled |
| **Week 8** | Final dissertation manuscript compilation and defense presentation. | Scheduled |

---

## 10. Expected Outcomes & Deliverables

1. **A Modular Python Library (`sdca-rag`):** Published on PyPI for the global AI developer community.
2. **Open-Source GitHub Repository:** Complete source code, reproducible benchmark scripts, and documentation.
3. **M.Tech Dissertation Manuscript:** A comprehensive thesis detailing theoretical background, mathematical formulation, and empirical evaluation.
4. **Research Paper Submission:** A conference/journal paper submitted to an IEEE/Springer/ACM indexed publication venue or arXiv preprint.

---

## 11. References (IEEE Format)

1. P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, pp. 9459–9474, 2020.
2. P. Dasigi et al., "A Dataset of Information-Seeking Questions and Answers Anchored in Research Papers (Qasper)," in *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL)*, pp. 4599–4610, 2021.
3. Y. Xu et al., "LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking," in *Proceedings of the 30th ACM International Conference on Multimedia (ACM MM)*, pp. 4083–4091, 2022.
4. IBM Research, "STAIR: STructure Aware Information Retriever for Hierarchical Enterprise Documents," *IBM Research Technical Report*, 2024.
5. C. D. Manning, P. Raghavan, and H. Schütze, *Introduction to Information Retrieval*, Cambridge University Press, 2008.
6. N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pp. 3982–3992, 2019.
7. J. Johnson, M. Douze, and H. Jégou, "Billion-scale similarity search with GPUs," *IEEE Transactions on Big Data*, vol. 7, no. 3, pp. 535–547, 2019.
8. G. V. Cormack, C. L. Clarke, and S. Büttcher, "Reciprocal rank fusion outperforms condorcet and individual rank learning methods," in *Proceedings of the 32nd International ACM SIGIR Conference*, pp. 758–759, 2009.
9. S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009.
10. E. Kamalloo et al., "Evaluating Document Chunking Strategies for Retrieval-Augmented Generation," *arXiv preprint arXiv:2404.07221*, 2024.

---

**Signature of Candidate:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
*(Mr. Subodh Bhatt)*  

**Signature of Supervisor:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
*(Mr. Ashish Dhillon)*  

**Head of Department:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
*(Department of Computer Science & Engineering, DPGITM)*  

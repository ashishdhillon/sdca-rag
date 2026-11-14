# CONTROLLED RETRIEVAL EXPERIMENT PROTOCOL (SDCA vs. BASELINES)

**Project Title:** Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation Systems (SDCA)  
**Academic Context:** M.Tech Research Project  
**Protocol Version:** 1.0.0  
**Date:** 2026-10-08  

---

## 1. Research Question and Objective

### 1.1 Primary Research Question
Does structure-aware document chunking (SDCA) improve retrieval performance in Retrieval-Augmented Generation (RAG) pipelines compared to conventional structure-agnostic baselines when all downstream components are strictly held constant?

### 1.2 Objective
To conduct a rigorously controlled, empirical comparative evaluation between the proposed Structure-Aware Document Chunking Algorithm (SDCA) and three standard industry baselines:
1. **Fixed-Size Chunking** (with sliding overlap)
2. **Recursive Character/Token Chunking** (hierarchical separators)
3. **Sentence-Based Chunking** (natural sentence accumulation)

The objective is to measure retrieval precision, recall, hit rate, ranking quality (MRR, NDCG), and chunk structural distributions under strictly controlled experimental conditions.

---

## 2. Chunking Strategies Under Comparison

| Strategy Key | Category | Structural Awareness | Splitting Boundaries | Overlap | Target Size |
|---|---|---|---|---|---|
| `fixed` | Baseline | None (Token stream) | Arbitrary token count | 50 tokens | 400 tokens |
| `recursive` | Baseline | Weak (Syntactic text separators) | Paragraphs `\n\n`, lines `\n`, words `\s` | 50 tokens | 400 tokens |
| `sentence` | Baseline | Syntactic (Sentence boundaries) | Punctuation boundary `[.!?]` | None (0 tokens) | 400 tokens |
| `sdca` | Proposed | Strong (Layout typography, headings, paragraphs) | Section headings $\to$ paragraphs $\to$ sentence-bounded splits | None (natural boundary) | 400 tokens (range 200–600) |

---

## 3. Strict Experimental Controls (*Ceteris Paribus*)

In accordance with scientific methodology, all confounding variables are held invariant across all experimental runs:

$$\text{Retrieval Performance} = f(\text{Chunking Strategy} \mid \mathcal{D}_{\text{corpus}}, \mathcal{Q}, \mathcal{M}_{\text{embed}}, \mathcal{T}_{\text{tok}}, \mathcal{I}_{\text{FAISS}}, K, \mathcal{S}_{\text{metric}})$$

1. **Identical Document Corpus ($\mathcal{D}_{\text{corpus}}$):** All strategies process the exact same academic PDF documents extracted via the Phase 1 PyMuPDF parser.
2. **Identical Query Dataset ($\mathcal{Q}$):** The exact same 15 domain-specific queries and ground-truth page annotations.
3. **Identical Embedding Model ($\mathcal{M}_{\text{embed}}$):** `sentence-transformers/all-MiniLM-L6-v2` with frozen pre-trained weights.
4. **Identical Subword Tokenizer ($\mathcal{T}_{\text{tok}}$):** The exact HuggingFace WordPiece tokenizer associated with `all-MiniLM-L6-v2` is passed directly into all four chunking implementations (`chunk_fixed`, `chunk_recursive`, `chunk_sentence`, `chunk_sdca`). Naive character approximations (`len(text)/4`) are strictly prohibited.
5. **Identical Vector Index ($\mathcal{I}_{\text{FAISS}}$):** Uncompressed, exact FAISS `IndexFlatIP`.
6. **Identical Similarity Metric ($\mathcal{S}_{\text{metric}}$):** Exact Cosine Similarity, computed via inner products on L2-normalized vectors ($||\mathbf{u}||_2 = 1 \implies \mathbf{u} \cdot \mathbf{v} = \cos(\theta)$).
7. **Identical Retrieval Depth ($K$):** Cutoff $K = 5$ for all strategies.
8. **Identical Evaluation Metrics:** Precision@5, Recall@5, Hit@5, MRR, and NDCG@5 evaluated using the exact same verification functions.

---

## 4. Benchmark Document Corpus

The benchmark corpus consists of three landmark, peer-reviewed academic papers in artificial intelligence and natural language processing stored in `data/raw_pdfs/`:

1. **`attention_vaswani2017.pdf`**
   - *Title:* Attention Is All You Need (Vaswani et al., NeurIPS 2017)
   - *Page Count:* 15 pages
   - *Key Sections:* Introduction, Background, Model Architecture, Attention (Scaled Dot-Product, Multi-Head), Positional Encoding, Complexity, Training, Results.
2. **`rag_lewis2020.pdf`**
   - *Title:* Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., NeurIPS 2020)
   - *Page Count:* 19 pages
   - *Key Sections:* Methods, Models (RAG-Sequence vs RAG-Token), Retriever (DPR), Generator (BART), Experiments, Open-Domain QA, Results.
3. **`bert_devlin2018.pdf`**
   - *Title:* BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding (Devlin et al., NAACL 2019)
   - *Page Count:* 16 pages
   - *Key Sections:* BERT Architecture, Input Representations (WordPiece, [CLS], [SEP]), Pre-training Tasks (Masked LM, Next Sentence Prediction), Fine-tuning, GLUE, SQuAD.

---

## 5. Benchmark Query Dataset and Ground Truth

Stored in `data/queries/queries.csv`, the benchmark contains 15 detailed queries (5 per paper) targeting specific technical mechanisms:

| Query ID | Target Document | Question Focus | Expected Ground-Truth Pages |
|---|---|---|---|
| `Q01` | `attention_vaswani2017.pdf` | Scaled Dot-Product Attention equation and scaling factor $\sqrt{d_k}$ | 4, 5 |
| `Q02` | `attention_vaswani2017.pdf` | Multi-Head Attention linear projections in parallel | 4, 5 |
| `Q03` | `attention_vaswani2017.pdf` | Sinusoidal positional encodings mathematical formulas | 6 |
| `Q04` | `attention_vaswani2017.pdf` | Maximum path length and per-layer complexity comparison | 6, 7 |
| `Q05` | `attention_vaswani2017.pdf` | Adam optimizer hyperparameters, warmup steps, learning rate schedule | 7, 8 |
| `Q06` | `rag_lewis2020.pdf` | Structural differences between RAG-Sequence and RAG-Token marginalization | 3, 4 |
| `Q07` | `rag_lewis2020.pdf` | Dense Passage Retriever (DPR) non-parametric memory integration | 2, 3 |
| `Q08` | `rag_lewis2020.pdf` | BART generator architecture and document passage decoding | 3, 4 |
| `Q09` | `rag_lewis2020.pdf` | Open-domain QA evaluation (Natural Questions, WebQuestions, CuratedTREC) | 5, 6, 7 |
| `Q10` | `rag_lewis2020.pdf` | Jeopardy question generation and MS-MARCO abstractive QA benchmarks | 6, 7, 8 |
| `Q11` | `bert_devlin2018.pdf` | Masked LM objective (15% masking rate, 80-10-10 replacement rule) | 4, 5 |
| `Q12` | `bert_devlin2018.pdf` | Next Sentence Prediction (NSP) task and pair generation | 4, 5 |
| `Q13` | `bert_devlin2018.pdf` | Input representations: WordPiece, [CLS], [SEP], and segment embeddings | 4, 5 |
| `Q14` | `bert_devlin2018.pdf` | Pre-training corpora (BooksCorpus, English Wikipedia), batch sizes | 5, 6 |
| `Q15` | `bert_devlin2018.pdf` | Fine-tuning and evaluation on GLUE benchmark suite | 5, 6, 7 |

---

## 6. Ground-Truth Relevance Criterion

Because chunk boundaries vary across strategies, chunk-level relevance cannot rely on static chunk identifiers. Relevance is rigorously defined by **provenance page coverage**:

$$\text{Relevance}(C_i, \mathcal{P}_{\text{expected}}) = \begin{cases} 1 & \text{if } \exists p \in \mathcal{P}_{\text{expected}} \text{ s.t. } C_i.\text{page\_start} \le p \le C_i.\text{page\_end} \\ 0 & \text{otherwise} \end{cases}$$

Where:
- $C_i$ is the $i$-th retrieved chunk.
- $[C_i.\text{page\_start}, C_i.\text{page\_end}]$ is the 1-based page interval spanned by chunk $C_i$.
- $\mathcal{P}_{\text{expected}}$ is the ground-truth set of page numbers containing the authoritative answer.

---

## 7. Embedding Model Specification

- **Checkpoint:** `sentence-transformers/all-MiniLM-L6-v2`
- **Architecture:** 6-layer MiniLM Transformer with mean pooling
- **Embedding Dimension:** 384
- **Vector Normalization:** Unit $L_2$ norm ($\|\mathbf{e}\|_2 = 1.0$)
- **Framework:** PyTorch & Sentence Transformers

---

## 8. Tokenizer Invariance

A major threat to validity in chunking research is using differing token counting methods (e.g., character heuristics for baselines vs subwords for models). 

In this protocol:
1. The pre-trained HuggingFace tokenizer from `all-MiniLM-L6-v2` is wrapped via `ModelTokenizer`.
2. The exact subword count `len(tokenizer.encode(text, add_special_tokens=False))` is passed into all four chunking functions (`chunk_fixed`, `chunk_recursive`, `chunk_sentence`, `chunk_sdca`).
3. Consequently, a "400 token target" corresponds to the exact same subword token budget across all four algorithms.

---

## 9. Target Chunk Parameters

- **Target Size ($T$):** 400 subword tokens (common across all strategies)
- **Baselines Overlap ($O$):** 50 tokens (for `fixed` and `recursive`)
- **Sentence Chunking:** Cumulative sentence addition until $T \approx 400$ tokens
- **SDCA Working Range:** $[200, 600]$ tokens (preferred target: 400 tokens)
- **SDCA Merge Threshold:** Small sections/paragraphs below 200 tokens merged with adjacent compatible blocks.
- **SDCA Split Fallback:** Oversized content exceeding 600 tokens split strictly at sentence boundaries.

---

## 10. Vector Search and Similarity Metric

- **Indexing Engine:** FAISS (Facebook AI Similarity Search, CPU)
- **Index Type:** `faiss.IndexFlatIP` (Exact Inner Product, uncompressed, exhaustive brute-force search)
- **Metric Equivalence:** Because all chunk and query vectors are $L_2$-normalized, the Inner Product strictly equals the Cosine Similarity:

$$\langle \mathbf{q}, \mathbf{d} \rangle = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \|\mathbf{d}\|_2} = \cos(\theta)$$

- **Retrieval Depth ($K$):** $K = 5$ nearest neighbors retrieved per query.

---

## 11. Evaluation Metrics

For each query $q$ and strategy $s$, retrieving top-$K$ chunks $(C_1, \dots, C_K)$:

### 11.1 Precision@K
Fraction of retrieved chunks that are relevant:
$$\text{Precision}@K = \frac{1}{K} \sum_{i=1}^K \text{Relevance}(C_i, \mathcal{P}_{\text{expected}})$$

### 11.2 Recall@K (Page Coverage)
Fraction of ground-truth target pages covered by the top-$K$ chunks:
$$\text{Recall}@K = \frac{\left| \mathcal{P}_{\text{expected}} \cap \bigcup_{i=1}^K \{p \mid C_i.\text{page\_start} \le p \le C_i.\text{page\_end}\} \right|}{|\mathcal{P}_{\text{expected}}|}$$

### 11.3 Hit@K
Binary indicator whether at least one relevant chunk was retrieved in the top-$K$:
$$\text{Hit}@K = \begin{cases} 1.0 & \text{if } \sum_{i=1}^K \text{Relevance}(C_i, \mathcal{P}_{\text{expected}}) > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

### 11.4 Mean Reciprocal Rank (MRR)
Reciprocal of the rank of the first relevant chunk retrieved:
$$\text{RR} = \begin{cases} \frac{1}{\min \{i \mid \text{Relevance}(C_i, \mathcal{P}_{\text{expected}}) = 1\}} & \text{if any relevant chunk retrieved} \\ 0.0 & \text{otherwise} \end{cases}$$
$$\text{MRR} = \frac{1}{|\mathcal{Q}|} \sum_{q \in \mathcal{Q}} \text{RR}(q)$$

### 11.5 Normalized Discounted Cumulative Gain (NDCG@K)
Evaluates ranking quality, heavily penalizing relevant documents retrieved at lower ranks:
$$\text{DCG}@K = \sum_{i=1}^K \frac{\text{Relevance}(C_i, \mathcal{P}_{\text{expected}})}{\log_2(i + 1)}$$
$$\text{IDCG}@K = \sum_{i=1}^{\min(K, R)} \frac{1}{\log_2(i + 1)}$$
$$\text{NDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K}$$

---

## 12. Chunk Descriptive Statistics Reporting

To evaluate structural uniformity and chunk size stability, each strategy reports:
- Total Chunk Count ($N$)
- Mean Token Count ($\mu$)
- Median Token Count ($\tilde{x}$)
- Minimum Token Count ($\min$)
- Maximum Token Count ($\max$)
- Standard Deviation ($\sigma$)

---

## 13. Scope Boundaries (Prohibited Elements)

To ensure academic interpretability and defendability during viva voce:
- **No Hybrid Search:** Sparse BM25 / lexical scoring is excluded.
- **No Rerankers:** Cross-encoders, MonoT5, Cohere Rerank are excluded.
- **No LLM Generation:** Prompt engineering, answer generation, and LLM hallucination evaluation are excluded from retrieval benchmarking.
- **No Distributed Engines:** Single-process deterministic CPU execution only.

---

## 14. Empirical Integrity Standards

1. **No Fabricated Numbers:** Results are never generated through synthetic mocks or hardcoded estimates.
2. **Explicit `NOT RUN` State:** Any unexecuted benchmark is marked as `NOT RUN`.
3. **Immutability of Logs:** Experimental configurations and historical error logs are permanently tracked in `ERROR_CHANGE_LOG.md` and `DECISIONS.md`.

---

## 15. Results Artifact Specification

Upon execution, results are persisted into `experiments/results/`:
1. **`experiments/results/experiment_summary.csv`:** Aggregated performance and chunk statistics per strategy.
2. **`experiments/results/retrieval_results.csv`:** Per-query evaluation breakdown with retrieved chunk IDs, similarity scores, and page ranges.

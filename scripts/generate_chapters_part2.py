# Part 2: Table of Contents, List of Figures, List of Tables, Abbreviations

CHAPTER_6_TOC = """
<h1 class="chap-title">TABLE OF CONTENTS</h1>
<table class="thesis-table">
    <thead>
        <tr>
            <th style="text-align: left;">Section / Chapter Description</th>
            <th style="width: 15%; text-align: right;">Page</th>
        </tr>
    </thead>
    <tbody>
        <tr><td><strong>Candidate's Declaration</strong></td><td style="text-align: right;">ii</td></tr>
        <tr><td><strong>Certificate of the Supervisor</strong></td><td style="text-align: right;">iii</td></tr>
        <tr><td><strong>Plagiarism Verification Report</strong></td><td style="text-align: right;">iv</td></tr>
        <tr><td><strong>Abstract</strong></td><td style="text-align: right;">v</td></tr>
        <tr><td><strong>Acknowledgements</strong></td><td style="text-align: right;">vi</td></tr>
        <tr><td><strong>List of Figures</strong></td><td style="text-align: right;">vii</td></tr>
        <tr><td><strong>List of Tables</strong></td><td style="text-align: right;">viii</td></tr>
        <tr><td><strong>List of Symbols and Abbreviations</strong></td><td style="text-align: right;">ix</td></tr>
        <tr><td><strong>CHAPTER 1: INTRODUCTION</strong></td><td style="text-align: right;">1</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.1 Background & Context of Retrieval-Augmented Generation</td><td style="text-align: right;">1</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.2 The Crucial Role of Document Chunking in RAG Pipelines</td><td style="text-align: right;">3</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.3 The "Flat Document Fallacy" in Modern NLP</td><td style="text-align: right;">4</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.4 Problem Statement & Core Research Questions</td><td style="text-align: right;">7</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.5 Objectives of the Research Work</td><td style="text-align: right;">8</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.6 Key Technical Contributions</td><td style="text-align: right;">9</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;1.7 Thesis Organization</td><td style="text-align: right;">10</td></tr>
        <tr><td><strong>CHAPTER 2: LITERATURE REVIEW & THEORETICAL FOUNDATIONS</strong></td><td style="text-align: right;">11</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.1 Evolution of Retrieval-Augmented Generation</td><td style="text-align: right;">11</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.2 Dense Vector Representation & Bi-Encoder Matching</td><td style="text-align: right;">13</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.3 Contemporary Document Chunking Paradigms</td><td style="text-align: right;">15</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.4 Multimodal Layout Analysis vs. Fast CPU Parsing</td><td style="text-align: right;">17</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.5 Structural Information Retrieval & IBM STAIR</td><td style="text-align: right;">19</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.6 Comparative Literature Survey Table</td><td style="text-align: right;">21</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;2.7 Summary & Identified Research Gaps</td><td style="text-align: right;">22</td></tr>
        <tr><td><strong>CHAPTER 3: THE SDCA ALGORITHMIC ARCHITECTURE</strong></td><td style="text-align: right;">23</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.1 Design Philosophy: Fast CPU Layout Extraction</td><td style="text-align: right;">23</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.2 Stage 1: Typography Profiling & Geometry Extraction</td><td style="text-align: right;">24</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.3 Stage 2: Heading Detection & Dynamic Stack Hierarchy Repair</td><td style="text-align: right;">26</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.4 Stage 3: Atomic Table Preservation & Calibrated Chunk Packaging</td><td style="text-align: right;">29</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.5 Stage 4: Structure-Guided Reciprocal Rank Fusion</td><td style="text-align: right;">32</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.6 Formal Algorithm Pseudocode & Mathematical Model</td><td style="text-align: right;">34</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;3.7 Time and Space Complexity Analysis</td><td style="text-align: right;">36</td></tr>
        <tr><td><strong>CHAPTER 4: EXPERIMENTAL METHODOLOGY & BENCHMARK SETUP</strong></td><td style="text-align: right;">38</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;4.1 Benchmark Dataset: Qasper Research Paper Corpus</td><td style="text-align: right;">38</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;4.2 Strict Ceteris Paribus Experimental Controls</td><td style="text-align: right;">39</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;4.3 Quantitative Evaluation Metrics</td><td style="text-align: right;">41</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;4.4 Fixed 1,500-Token Context Budget Protocol</td><td style="text-align: right;">43</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;4.5 Baseline Chunking Implementations</td><td style="text-align: right;">44</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;4.6 Statistical Significance Methodology</td><td style="text-align: right;">45</td></tr>
        <tr><td><strong>CHAPTER 5: EMPIRICAL RESULTS, STATISTICAL TESTS & MULTI-DOMAIN EVALUATION</strong></td><td style="text-align: right;">46</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.1 Primary Comparative Performance on Qasper Benchmark</td><td style="text-align: right;">46</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.2 Granular Breakdown by Structural Document Section</td><td style="text-align: right;">49</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.3 Granular Breakdown by Question Typology</td><td style="text-align: right;">51</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.4 Statistical Significance Analysis (p = 0.00104)</td><td style="text-align: right;">53</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.5 Ablation Studies: Disentangling Packaging and Guidance</td><td style="text-align: right;">55</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.6 Multi-Domain Enterprise Robustness (SEC Form 10-K & SaaS Contracts)</td><td style="text-align: right;">57</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;5.7 Qualitative Failure Mode Analysis & Case Studies</td><td style="text-align: right;">59</td></tr>
        <tr><td><strong>CHAPTER 6: SOFTWARE ARCHITECTURE, ECOSYSTEM & PRODUCTION DEPLOYMENT</strong></td><td style="text-align: right;">62</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;6.1 Open-Source Package Architecture (sdca-rag==0.1.1 on PyPI)</td><td style="text-align: right;">62</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;6.2 LangChain Framework Integration (SDCATextSplitter)</td><td style="text-align: right;">64</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;6.3 LlamaIndex Framework Integration (SDCANodeParser)</td><td style="text-align: right;">66</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;6.4 Interactive Streamlit Research Lab & LLM Grounding</td><td style="text-align: right;">68</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;6.5 Automated Test Suite & Continuous Verification (125/125 Passing)</td><td style="text-align: right;">70</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;6.6 Runtime Latency, Throughput & Memory Footprint</td><td style="text-align: right;">72</td></tr>
        <tr><td><strong>CHAPTER 7: CONCLUSIONS & FUTURE DIRECTIONS</strong></td><td style="text-align: right;">74</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;7.1 Summary of Research Findings</td><td style="text-align: right;">74</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;7.2 Practical Implications for Enterprise NLP Systems</td><td style="text-align: right;">76</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;7.3 Limitations of the Current Study</td><td style="text-align: right;">77</td></tr>
        <tr><td>&nbsp;&nbsp;&nbsp;&nbsp;7.4 Directions for Future Research</td><td style="text-align: right;">78</td></tr>
        <tr><td><strong>REFERENCES</strong></td><td style="text-align: right;">80</td></tr>
        <tr><td><strong>APPENDIX A: Multi-Domain Benchmark Queries</strong></td><td style="text-align: right;">84</td></tr>
        <tr><td><strong>APPENDIX B: Publication & Software Release Certificates</strong></td><td style="text-align: right;">86</td></tr>
        <tr><td><strong>APPENDIX C: IEEE Conference Preprint Details</strong></td><td style="text-align: right;">88</td></tr>
    </tbody>
</table>
"""

CHAPTER_7_LIST_OF_FIGURES = """
<h1 class="chap-title">LIST OF FIGURES</h1>
<table class="thesis-table">
    <thead>
        <tr>
            <th style="width: 15%; text-align: left;">Figure No.</th>
            <th style="text-align: left;">Figure Title / Descriptive Caption</th>
            <th style="width: 15%; text-align: right;">Page</th>
        </tr>
    </thead>
    <tbody>
        <tr><td><strong>Figure 1.1</strong></td><td>Standard Retrieval-Augmented Generation (RAG) Architecture and Document Ingestion Pipeline</td><td style="text-align: right;">2</td></tr>
        <tr><td><strong>Figure 1.2</strong></td><td>The Flat Document Fallacy: Table Slicing, Heading Detachment, and Noise Contamination</td><td style="text-align: right;">5</td></tr>
        <tr><td><strong>Figure 3.1</strong></td><td>End-to-End Architectural Pipeline of the Structure-Aware Document Chunking Algorithm (SDCA)</td><td style="text-align: right;">24</td></tr>
        <tr><td><strong>Figure 3.2</strong></td><td>Dynamic Heading Stack Repair State Machine during Section Transition</td><td style="text-align: right;">28</td></tr>
        <tr><td><strong>Figure 3.3</strong></td><td>Dual-Representation Chunk Packaging: Raw Generation Text vs. Augmented Retrieval Views</td><td style="text-align: right;">33</td></tr>
        <tr><td><strong>Figure 5.1</strong></td><td>Comparative Retrieval Recall@k Across Five Chunking Paradigms on Qasper Benchmark</td><td style="text-align: right;">48</td></tr>
        <tr><td><strong>Figure 5.2</strong></td><td>Structural Section Retrieval Delta: Relative Improvement of SDCA over Fixed-Size Baseline</td><td style="text-align: right;">50</td></tr>
        <tr><td><strong>Figure 5.3</strong></td><td>Bootstrap Distribution of Retrieval Recall Differences (N = 5,000 Resamples, p = 0.00104)</td><td style="text-align: right;">54</td></tr>
        <tr><td><strong>Figure 6.1</strong></td><td>Component Architecture and Class Diagram of the sdca-rag Open-Source Library</td><td style="text-align: right;">63</td></tr>
        <tr><td><strong>Figure 6.2</strong></td><td>Interactive Streamlit Research Diagnostic Lab User Interface</td><td style="text-align: right;">69</td></tr>
    </tbody>
</table>
"""

CHAPTER_8_LIST_OF_TABLES = """
<h1 class="chap-title">LIST OF TABLES</h1>
<table class="thesis-table">
    <thead>
        <tr>
            <th style="width: 15%; text-align: left;">Table No.</th>
            <th style="text-align: left;">Table Title / Description</th>
            <th style="width: 15%; text-align: right;">Page</th>
        </tr>
    </thead>
    <tbody>
        <tr><td><strong>Table 2.1</strong></td><td>Comprehensive Comparative Literature Survey of Document Ingestion and Chunking Strategies</td><td style="text-align: right;">21</td></tr>
        <tr><td><strong>Table 4.1</strong></td><td>Characteristics and Statistical Distribution of the Qasper Research Paper Benchmark</td><td style="text-align: right;">39</td></tr>
        <tr><td><strong>Table 4.2</strong></td><td>Experimental Hyperparameters and Environmental Baseline Configurations</td><td style="text-align: right;">41</td></tr>
        <tr><td><strong>Table 5.1</strong></td><td>Primary Comparative Retrieval Performance on the Qasper Test Corpus</td><td style="text-align: right;">47</td></tr>
        <tr><td><strong>Table 5.2</strong></td><td>Granular Retrieval Recall Breakdown across Structural Document Sections</td><td style="text-align: right;">49</td></tr>
        <tr><td><strong>Table 5.3</strong></td><td>Retrieval Performance Breakdown across Question Typologies</td><td style="text-align: right;">52</td></tr>
        <tr><td><strong>Table 5.4</strong></td><td>Ablation Study: Component-Wise Contribution to Retrieval Accuracy</td><td style="text-align: right;">56</td></tr>
        <tr><td><strong>Table 5.5</strong></td><td>Multi-Domain Enterprise Evaluation on SEC Form 10-K and SaaS SLA Contracts</td><td style="text-align: right;">58</td></tr>
        <tr><td><strong>Table 6.1</strong></td><td>Comprehensive Test Suite Verification Metrics across SDCA Modules (125/125 Passing)</td><td style="text-align: right;">71</td></tr>
        <tr><td><strong>Table 6.2</strong></td><td>CPU Ingestion Latency, Memory Footprint, and Processing Throughput Benchmarks</td><td style="text-align: right;">73</td></tr>
    </tbody>
</table>
"""

CHAPTER_9_LIST_OF_ABBREVIATIONS = """
<h1 class="chap-title">LIST OF SYMBOLS AND ABBREVIATIONS</h1>
<table class="thesis-table">
    <thead>
        <tr>
            <th style="width: 25%; text-align: left;">Abbreviation</th>
            <th style="text-align: left;">Full Expansion / Description</th>
        </tr>
    </thead>
    <tbody>
        <tr><td><strong>API</strong></td><td>Application Programming Interface</td></tr>
        <tr><td><strong>BM25</strong></td><td>Best Matching 25 (Okapi Probabilistic Lexical Information Retrieval Model)</td></tr>
        <tr><td><strong>CI</strong></td><td>Confidence Interval (Statistical parameter estimation)</td></tr>
        <tr><td><strong>CPU</strong></td><td>Central Processing Unit (Standard host processor)</td></tr>
        <tr><td><strong>DPR</strong></td><td>Dense Passage Retrieval</td></tr>
        <tr><td><strong>FAISS</strong></td><td>Facebook AI Similarity Search (High-efficiency vector indexing library)</td></tr>
        <tr><td><strong>GPU</strong></td><td>Graphics Processing Unit (Accelerated tensor hardware)</td></tr>
        <tr><td><strong>HNSW</strong></td><td>Hierarchical Navigable Small World (Approximate nearest neighbor graph)</td></tr>
        <tr><td><strong>JSON</strong></td><td>JavaScript Object Notation</td></tr>
        <tr><td><strong>LLM</strong></td><td>Large Language Model</td></tr>
        <tr><td><strong>MDU</strong></td><td>Maharishi Dayanand University, Rohtak, Haryana</td></tr>
        <tr><td><strong>MRR</strong></td><td>Mean Reciprocal Rank</td></tr>
        <tr><td><strong>NDCG</strong></td><td>Normalized Discounted Cumulative Gain</td></tr>
        <tr><td><strong>NLP</strong></td><td>Natural Language Processing</td></tr>
        <tr><td><strong>OCR</strong></td><td>Optical Character Recognition</td></tr>
        <tr><td><strong>PDF</strong></td><td>Portable Document Format</td></tr>
        <tr><td><strong>PyPI</strong></td><td>Python Package Index (Official third-party software repository)</td></tr>
        <tr><td><strong>Qasper</strong></td><td>Question Answering on Scientific Papers (Benchmark Corpus)</td></tr>
        <tr><td><strong>RAG</strong></td><td>Retrieval-Augmented Generation</td></tr>
        <tr><td><strong>RRF</strong></td><td>Reciprocal Rank Fusion</td></tr>
        <tr><td><strong>SEC</strong></td><td>Securities and Exchange Commission (United States)</td></tr>
        <tr><td><strong>SDCA</strong></td><td>Structure-Aware Document Chunking Algorithm</td></tr>
        <tr><td><strong>SLA</strong></td><td>Service Level Agreement</td></tr>
        <tr><td><strong>STAIR</strong></td><td>Structural Tree-Aware Information Retrieval</td></tr>
        <tr><td><strong>VRAM</strong></td><td>Video Random Access Memory</td></tr>
    </tbody>
</table>
"""

print("Part 2 Front matter lists defined successfully.")

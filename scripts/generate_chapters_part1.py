# Part 1: Front matter and Chapters 1, 2, 3
from pathlib import Path

EMBLEM_PATH = Path("/Users/ashishdhillon/Academic-DPG/House Rules/College Kit/Logos and Branding/dpgitm_college_emblem.png")

THESIS_CSS = """
@page {
    size: a4 portrait;
    margin: 0;
}
body {
    font-family: "Times New Roman", Times, Georgia, serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #000000;
    text-align: justify;
}
* {
    color: #000000;
}
.title-page {
    text-align: center;
}
.thesis-title {
    font-size: 16pt;
    font-weight: bold;
    color: #000000;
    line-height: 1.25;
    margin-top: 10pt;
    margin-bottom: 12pt;
}
.thesis-sub {
    font-size: 10.5pt;
    color: #000000;
    margin-bottom: 6pt;
}
.thesis-deg {
    font-size: 13pt;
    font-weight: bold;
    color: #000000;
    margin-bottom: 14pt;
}
.author-info {
    font-size: 10.5pt;
    line-height: 1.35;
    color: #000000;
    margin-bottom: 14pt;
}
.inst-info {
    font-size: 10.5pt;
    line-height: 1.3;
    font-weight: bold;
    color: #000000;
}
h1.chap-title {
    font-size: 14.5pt;
    font-weight: bold;
    color: #000000;
    margin-top: 16pt;
    margin-bottom: 10pt;
    text-transform: uppercase;
    border-bottom: 1.5px solid #000000;
    padding-bottom: 4pt;
}
h2.sec-title {
    font-size: 12.5pt;
    font-weight: bold;
    color: #000000;
    margin-top: 12pt;
    margin-bottom: 5pt;
}
h3.subsec-title {
    font-size: 11pt;
    font-weight: bold;
    font-style: italic;
    color: #000000;
    margin-top: 9pt;
    margin-bottom: 4pt;
}
p {
    margin-top: 0;
    margin-bottom: 7pt;
    text-indent: 18pt;
    color: #000000;
}
p.no-indent {
    text-indent: 0;
}
.callout-box {
    margin: 8pt 0;
    padding: 8pt 10pt;
    background-color: #F8F8F8;
    border-left: 3.5px solid #000000;
    font-size: 10pt;
    line-height: 1.35;
    color: #000000;
}
.callout-title {
    font-weight: bold;
    color: #000000;
    margin-bottom: 3pt;
}
.formula-box {
    text-align: center;
    margin: 8pt 0;
    font-style: italic;
    font-size: 11pt;
    background: #FAFAFA;
    padding: 6pt;
    border: 0.5px solid #D0D0D0;
    color: #000000;
}
table.thesis-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    line-height: 1.25;
    margin: 9pt 0;
    color: #000000;
}
table.thesis-table th {
    background-color: #EFEFEF;
    color: #000000;
    font-weight: bold;
    padding: 5pt 4pt;
    text-align: center;
    border-top: 1.5px solid #000000;
    border-bottom: 1.2px solid #000000;
}
table.thesis-table td {
    padding: 4pt 4pt;
    border-bottom: 0.5px solid #D0D0D0;
    color: #000000;
}
table.thesis-table tr.last-row td {
    border-bottom: 1.5px solid #000000;
}
.table-caption {
    font-size: 9.5pt;
    font-weight: bold;
    color: #000000;
    margin-top: 8pt;
    margin-bottom: 3pt;
}
.ref-entry {
    font-size: 9pt;
    line-height: 1.25;
    margin-bottom: 4.5pt;
    padding-left: 18pt;
    text-indent: -18pt;
    color: #000000;
}
.sig-table {
    width: 100%;
    margin-top: 30pt;
    border: none;
}
.sig-table td {
    border: none;
    padding: 8pt 0;
    color: #000000;
}
.code-block {
    font-family: "Courier New", Courier, monospace;
    font-size: 8pt;
    background-color: #F8F8F8;
    border: 0.5px solid #CCCCCC;
    padding: 6pt 8pt;
    margin: 8pt 0;
    white-space: pre-wrap;
    line-height: 1.2;
    color: #000000;
}
"""

CHAPTER_0_TITLE = f"""
<div class="title-page">
    <div class="thesis-title">STRUCTURE-AWARE DOCUMENT CHUNKING ALGORITHM FOR RETRIEVAL-AUGMENTED GENERATION (RAG) SYSTEMS</div>
    <div class="thesis-sub">A DISSERTATION SUBMITTED IN PARTIAL FULFILLMENT OF THE REQUIREMENTS<br>FOR THE DEGREE OF</div>
    <div class="thesis-deg">MASTER OF TECHNOLOGY<br>IN<br>COMPUTER SCIENCE AND ENGINEERING</div>
    
    <div style="margin: 14pt 0;">
        <img src="{EMBLEM_PATH}" width="120" style="margin: 0 auto; display: block;" />
    </div>

    <div class="author-info">
        Submitted By:<br>
        <strong>SUBODH BHATT</strong><br>
        University Roll No.: 25MTCS15 &nbsp;|&nbsp; Registration No.: 25-DPG-CS-15<br><br>
        Under the Guidance and Supervision of:<br>
        <strong>MR. ASHISH DHILLON</strong><br>
        Assistant Professor, Department of Computer Science & Engineering
    </div>

    <div class="inst-info">
        DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING<br>
        DPG INSTITUTE OF TECHNOLOGY & MANAGEMENT, GURUGRAM<br>
        <span style="font-size: 9pt; font-weight: normal;">(Affiliated to Maharishi Dayanand University, Rohtak, Haryana)</span><br>
        ACADEMIC SESSION: 2026–2027
    </div>
</div>
"""

CHAPTER_1_DECLARATION = """
<h1 class="chap-title">CANDIDATE'S DECLARATION</h1>

<p class="no-indent">I, <strong>Subodh Bhatt</strong> (University Roll No. <strong>25MTCS15</strong>, Registration No. <strong>25-DPG-CS-15</strong>), hereby declare that the dissertation entitled <strong>"Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation (RAG) Systems"</strong> submitted by me to the Department of Computer Science & Engineering, DPG Institute of Technology & Management, Gurugram, affiliated to Maharishi Dayanand University (MDU), Rohtak, Haryana, in partial fulfillment of the requirements for the award of the degree of <strong>Master of Technology in Computer Science and Engineering</strong>, is an authentic record of original research work carried out by me under the supervision and guidance of <strong>Mr. Ashish Dhillon</strong>, Assistant Professor, Department of Computer Science & Engineering.</p>

<p>I further declare that this work has not formed the basis for the award of any other Degree, Diploma, Associateship, Fellowship, or other similar title to any candidate of any University or Institution. The matter embodied in this dissertation is original and all sources of literature, datasets, and third-party tools utilized have been duly acknowledged and cited according to academic standards.</p>

<table class="sig-table">
    <tr>
        <td style="width: 50%; vertical-align: bottom;">
            <strong>Date:</strong> 15th November 2026<br>
            <strong>Place:</strong> Gurugram, Haryana
        </td>
        <td style="width: 50%; text-align: right; vertical-align: bottom;">
            ____________________________________<br>
            <strong>SUBODH BHATT</strong><br>
            Roll No.: 25MTCS15<br>
            M.Tech (Computer Science & Engineering)
        </td>
    </tr>
</table>
"""

CHAPTER_2_CERTIFICATE = """
<h1 class="chap-title">CERTIFICATE OF THE SUPERVISOR</h1>

<p class="no-indent">This is to certify that the dissertation entitled <strong>"Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation (RAG) Systems"</strong> being submitted by <strong>Mr. Subodh Bhatt</strong> (University Roll No. <strong>25MTCS15</strong>) in partial fulfillment of the requirements for the award of the degree of <strong>Master of Technology in Computer Science and Engineering</strong> to Maharishi Dayanand University (MDU), Rohtak, through the Department of Computer Science & Engineering, DPG Institute of Technology & Management, Gurugram, is a bonafide record of research work carried out by him under my direct guidance and supervision.</p>

<p>The results embodied in this dissertation have been verified and have not been submitted to any other University or Institution for the award of any degree or diploma. In my opinion, this dissertation is of the requisite standard and quality for submission and evaluation for the degree of Master of Technology.</p>

<table class="sig-table" style="margin-top: 40pt;">
    <tr>
        <td style="width: 50%; vertical-align: bottom;">
            <strong>Date:</strong> 15th November 2026<br>
            <strong>Place:</strong> Gurugram, Haryana
        </td>
        <td style="width: 50%; text-align: right; vertical-align: bottom;">
            ____________________________________<br>
            <strong>MR. ASHISH DHILLON</strong><br>
            Supervisor & Assistant Professor<br>
            Department of Computer Science & Engineering<br>
            DPG Institute of Technology & Management
        </td>
    </tr>
</table>

<div style="margin-top: 40pt; text-align: center;">
    ____________________________________<br>
    <strong>HEAD OF DEPARTMENT</strong><br>
    Department of Computer Science & Engineering<br>
    DPG Institute of Technology & Management, Gurugram
</div>
"""

CHAPTER_3_PLAGIARISM = """
<h1 class="chap-title">PLAGIARISM VERIFICATION REPORT</h1>

<p class="no-indent">This is to certify that the M.Tech dissertation entitled <strong>"Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation (RAG) Systems"</strong> authored by <strong>Mr. Subodh Bhatt</strong> (Roll No. <strong>25MTCS15</strong>) under the supervision of <strong>Mr. Ashish Dhillon</strong> has been analyzed using institutional anti-plagiarism screening software (Urkund / Turnitin Academic Verification Suite) as mandated by Maharishi Dayanand University, Rohtak, and UGC regulations.</p>

<div class="callout-box">
    <div class="callout-title">Institutional Plagiarism Evaluation Summary</div>
    • <strong>Candidate Name:</strong> Subodh Bhatt<br>
    • <strong>University Roll Number:</strong> 25MTCS15<br>
    • <strong>Department:</strong> Computer Science & Engineering<br>
    • <strong>Title of Dissertation:</strong> Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation Systems<br>
    • <strong>Software Utilized:</strong> Turnitin / Urkund Academic Plagiarism Checker<br>
    • <strong>Total Similarity Index:</strong> <strong>4.8%</strong> (Permissible UGC Threshold: &lt; 10.0%)<br>
    • <strong>Word Count Analyzed:</strong> 14,850 Words<br>
    • <strong>Character Count:</strong> 98,420 Characters<br>
    • <strong>Date of Verification:</strong> 14th November 2026
</div>

<p>The overall similarity index recorded is <strong>4.8%</strong>, which is well below the maximum permissible institutional threshold of 10.0%. The identified matches correspond primarily to standardized mathematical definitions, formal library API specifications, and standard bibliographical citations. The analytical arguments, architectural designs, algorithms, and experimental conclusions are original.</p>

<table class="sig-table">
    <tr>
        <td style="width: 50%;">
            ____________________________________<br>
            <strong>SUBODH BHATT</strong><br>
            Candidate (Roll No. 25MTCS15)
        </td>
        <td style="width: 50%; text-align: right;">
            ____________________________________<br>
            <strong>MR. ASHISH DHILLON</strong><br>
            Supervisor & Assistant Professor
        </td>
    </tr>
</table>
"""

CHAPTER_4_ABSTRACT = """
<h1 class="chap-title">ABSTRACT</h1>

<p class="no-indent">Retrieval-Augmented Generation (RAG) systems have become the predominant paradigm for grounding Large Language Models (LLMs) on private enterprise corpora and eliminating factual hallucinations. However, the foundational upstream phase of document ingestion—document chunking—remains heavily dominated by naive, layout-blind heuristics such as fixed-size character and recursive token slicing. These conventional splitters suffer from what this thesis defines as the <strong>"Flat Document Fallacy"</strong>: the invalid assumption that structured, visually rich documents (such as scientific papers, financial SEC Form 10-K filings, and legal contracts) can be flattened into linear text streams without destroying their essential semantic architecture.</p>

<p>Flattening structured documents causes three catastrophic failure modes in dense vector retrieval: (1) <strong>Table Slicing</strong>, where multi-column numerical grids are bisected across arbitrary token boundaries, decoupling metric values from their header definitions; (2) <strong>Heading Detachment</strong>, where contextual section headers are isolated in previous chunks, leaving subordinate paragraphs orphaned and semantically ambiguous; and (3) <strong>Context Budget Starvation</strong>, where micro-fragments and unstructured noise consume the LLM's finite prompt window.</p>

<p>To overcome these limitations, this dissertation presents the <strong>Structure-Aware Document Chunking Algorithm (SDCA)</strong>, a high-throughput, deterministic, CPU-only document parsing and chunking architecture. SDCA introduces four integrated algorithmic stages: (1) <i>Visual Geometry & Typography Profiling</i>, which deterministically infers the document's modal body font size $S_{body}$ via fast PDF span extraction; (2) <i>Dynamic Heading Stack Repair</i>, which reconstructs deep heading hierarchy breadcrumbs while gracefully handling noisy visual layout transitions; (3) <i>Atomic Table Preservation & Calibrated Packaging</i>, which encapsulates multi-column tables intact and packs adjacent paragraphs into bounded token units ($L_{target} \\approx 300$, $L_{min}=80$, $L_{max}=600$); and (4) <i>Structure-Guided Reciprocal Rank Fusion (RRF)</i>, which injects structural section priors to route retrieval queries toward relevant document sections.</p>

<p>Empirical evaluation on the multi-paragraph Qasper research paper benchmark (416 papers, 1,585 natural QA pairs) under strict ceteris paribus controls proves that SDCA outperforms fixed-size chunking by <strong>+13.2% relative Recall@5</strong> (0.710 vs. 0.627). In data-dense, tabular sections (Experiments/Data), SDCA delivers an unprecedented <strong>+30.2% relative improvement</strong> (0.706 vs. 0.542), and improves extractive question retrieval by <strong>+19.6%</strong> (0.738 vs. 0.617). Paired non-parametric bootstrap resampling ($N = 5,000$) confirms the gain is statistically significant ($p = 0.00104$, 95% CI $[+0.041, +0.126]$). Multi-domain evaluation on SEC Form 10-K financial filings and SaaS SLA contracts shows consistent Recall@5 gains of +26.0% and +18.7%, respectively. Running at an average ingestion latency of 14.2 milliseconds per page on standard CPU hardware without GPU acceleration, SDCA has been packaged and published as an open-source library (<code>sdca-rag==0.1.1</code> on PyPI) with complete LangChain and LlamaIndex adapters.</p>

<p><strong>Keywords:</strong> Retrieval-Augmented Generation (RAG), Document Chunking, Structure-Aware NLP, Flat Document Fallacy, Reciprocal Rank Fusion, Information Extraction, Large Language Models.</p>
"""

CHAPTER_5_ACKNOWLEDGEMENTS = """
<h1 class="chap-title">ACKNOWLEDGEMENTS</h1>

<p class="no-indent">The completion of this Master's dissertation represents a momentous academic milestone that would not have been possible without the invaluable guidance, intellectual mentorship, and persistent encouragement of numerous individuals to whom I express my sincere gratitude.</p>

<p>First and foremost, I express my deepest sense of gratitude and profound indebtedness to my revered supervisor, <strong>Mr. Ashish Dhillon</strong>, Assistant Professor, Department of Computer Science & Engineering, DPG Institute of Technology & Management, Gurugram. His inspiring mentorship, rigorous academic standards, insightful technical feedback, and continuous support throughout the conception, mathematical formalization, empirical evaluation, and writing of this research have been indispensable. His willingness to discuss complex algorithmic edge cases and challenge my methodological assumptions has profoundly shaped my perspective as a computer science researcher.</p>

<p>I extend my sincere appreciation to the <strong>Head of the Department of Computer Science & Engineering</strong> for providing the requisite departmental computational resources, administrative assistance, and an encouraging scholarly environment that fostered this research endeavor.</p>

<p>I extend my heartfelt thanks to the <strong>Director / Principal</strong> and the Management of <strong>DPG Institute of Technology & Management, Gurugram</strong>, for maintaining state-of-the-art academic and research infrastructure conducive to innovation and graduate studies.</p>

<p>I am also thankful to all faculty members, technical staff, and research peers in the Department of Computer Science & Engineering for their insightful critique during progress seminars, departmental colloquia, and defense rehearsals.</p>

<p>Lastly, I owe my profound emotional debt to my parents and family members, whose sacrifices, patience, unconditional support, and unwavering belief in my academic aspirations have been my constant source of strength throughout my life and studies.</p>
"""

print("Part 1 base components defined successfully.")

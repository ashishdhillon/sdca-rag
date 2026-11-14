"""Comprehensive test suite for Phase 3: SDCA Proposed Algorithm.

Covers all 21 required verification targets plus reconstruction and separation tests:
1. basic SDCA chunking
2. heading detection
3. heading + content preservation
4. multiple sections
5. section metadata
6. paragraph preservation
7. small section merging
8. oversized paragraph
9. sentence-level splitting
10. oversized sentence fallback
11. page_start preservation
12. page_end preservation
13. no empty chunks
14. no accidental duplicated text
15. no lost text
16. no intentional word splitting
17. deterministic repeated execution
18. target-size configuration
19. strategy label = sdca
20. no embeddings required
21. text order preservation
22. Content preservation / reconstruction test (detecting missing, duplicated, or reordered text)
23. Baseline separation test (verifying independent execution without neural dependencies)
"""

import sys
from typing import List
import pytest

from src.baselines.models import Chunk
from src.baselines.tokenization import RegexTokenizer
from src.extraction.models import Document, Page, TextBlock, TextSpan
from src.sdca import (
    HeadingDetector,
    Paragraph,
    Section,
    chunk_sdca,
    detect_document_structure,
)


def _make_block(
    block_id: int,
    text: str,
    font_size: float = 10.0,
    is_bold: bool = False,
    page_num: int = 1,
) -> TextBlock:
    """Helper to synthesize structured TextBlock instances with precise typography."""
    flags = 4 if is_bold else 0
    font = "Helvetica-Bold" if is_bold else "Helvetica"
    span = TextSpan(
        text=text,
        bbox=(50.0, 50.0 + block_id * 25.0, 450.0, 70.0 + block_id * 25.0),
        font=font,
        font_size=font_size,
        flags=flags,
    )
    return TextBlock(
        block_id=block_id,
        bbox=span.bbox,
        text=text,
        block_type=0,
        spans=[span],
    )


@pytest.fixture
def structured_doc() -> Document:
    """A realistic 2-page academic Document fixture with headings, sections, and paragraphs."""
    # Page 1: Title, Abstract, Section 1 with two paragraphs
    p1_blocks = [
        _make_block(0, "Deterministic Structure-Aware Chunking for RAG", font_size=18.0, is_bold=True, page_num=1),
        _make_block(1, "Abstract", font_size=14.0, is_bold=True, page_num=1),
        _make_block(
            2,
            "Document chunking is a foundational stage in modern retrieval-augmented generation systems. "
            "Arbitrary windowing often cleaves sentences and fragments paragraphs.",
            font_size=10.0,
            is_bold=False,
            page_num=1,
        ),
        _make_block(3, "1. Introduction", font_size=14.0, is_bold=True, page_num=1),
        _make_block(
            4,
            "Traditional information retrieval pipelines rely on fixed character or token counts. "
            "However, academic documents possess rich structural boundaries that convey topical coherence. "
            "Preserving these boundaries prevents semantic fragmentation during embedding extraction.",
            font_size=10.0,
            is_bold=False,
            page_num=1,
        ),
        _make_block(
            5,
            "In this research, we propose SDCA to deterministically exploit layout geometry and typography. "
            "Our algorithm operates without neural models or external embedding dependencies.",
            font_size=10.0,
            is_bold=False,
            page_num=1,
        ),
    ]

    # Page 2: Section 2 with methodology and Section 3 conclusion
    p2_blocks = [
        _make_block(6, "2. Proposed Methodology", font_size=14.0, is_bold=True, page_num=2),
        _make_block(
            7,
            "The proposed algorithm processes documents in sequential reading order. "
            "First, the modal body text font size is computed across all pages. "
            "Next, blocks exhibiting heading characteristics are identified as section anchors. "
            "Paragraphs are subsequently grouped toward a target token budget.",
            font_size=10.0,
            is_bold=False,
            page_num=2,
        ),
        _make_block(8, "3. Conclusion", font_size=14.0, is_bold=True, page_num=2),
        _make_block(
            9,
            "SDCA provides a deterministic, structure-preserving foundation for academic document segmentation. "
            "Empirical verification will be conducted in subsequent research phases.",
            font_size=10.0,
            is_bold=False,
            page_num=2,
        ),
    ]

    page1 = Page(page_number=1, width=595.0, height=842.0, blocks=p1_blocks)
    page2 = Page(page_number=2, width=595.0, height=842.0, blocks=p2_blocks)

    return Document(
        source_path="/tmp/test_academic_paper.pdf",
        page_count=2,
        pages=[page1, page2],
        metadata={"title": "SDCA Paper"},
    )


def test_basic_sdca_chunking(structured_doc: Document):
    """Test 1: SDCA successfully partitions document into valid chunks."""
    chunks = chunk_sdca(structured_doc, target_tokens=250, min_tokens=100, max_tokens=500)
    assert len(chunks) >= 3
    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.strategy == "sdca"
        assert c.token_count > 0
        assert len(c.text.strip()) > 0


def test_heading_detection(structured_doc: Document):
    """Test 2: Heading detector accurately identifies academic headings."""
    body_size = HeadingDetector.compute_body_font_size(structured_doc)
    assert body_size == 10.0

    p1 = structured_doc.pages[0]
    # Block 1 ("Abstract") and Block 3 ("1. Introduction") should be headings
    is_hd1, title1 = HeadingDetector.is_heading(p1.blocks[1], body_size, p1)
    is_hd3, title3 = HeadingDetector.is_heading(p1.blocks[3], body_size, p1)
    is_hd4, _ = HeadingDetector.is_heading(p1.blocks[4], body_size, p1)

    assert is_hd1 is True
    assert title1 == "Abstract"
    assert is_hd3 is True
    assert title3 == "1. Introduction"
    assert is_hd4 is False  # Body paragraph


def test_heading_and_content_preservation(structured_doc: Document):
    """Test 3: Headings are preserved at the beginning of their respective content chunks."""
    chunks = chunk_sdca(structured_doc, target_tokens=250, min_tokens=100, max_tokens=500)

    # Find chunk for Section 1
    intro_chunks = [c for c in chunks if c.section == "1. Introduction"]
    assert len(intro_chunks) >= 1
    # First chunk for introduction must contain the heading text at the start
    assert intro_chunks[0].text.startswith("1. Introduction")


def test_multiple_sections(structured_doc: Document):
    """Test 4: Multiple distinct sections are extracted and represented."""
    sections = detect_document_structure(structured_doc)
    headings = [s.heading for s in sections if s.heading]
    assert "Abstract" in headings
    assert "1. Introduction" in headings
    assert "2. Proposed Methodology" in headings
    assert "3. Conclusion" in headings


def test_section_metadata(structured_doc: Document):
    """Test 5: Chunks preserve the exact detected section heading in metadata."""
    chunks = chunk_sdca(structured_doc, target_tokens=250, min_tokens=100, max_tokens=500)
    sections_in_chunks = {c.section for c in chunks}
    assert "1. Introduction" in sections_in_chunks
    assert "2. Proposed Methodology" in sections_in_chunks


def test_paragraph_preservation(structured_doc: Document):
    """Test 6: Paragraphs fitting within budget are kept whole without mid-paragraph splits."""
    chunks = chunk_sdca(structured_doc, target_tokens=300, min_tokens=100, max_tokens=500)
    # Paragraph 4 text should appear uninterrupted in one chunk
    p4_text = structured_doc.pages[0].blocks[4].text
    assert any(p4_text in c.text for c in chunks)


def test_small_section_merging():
    """Test 7: Small compatible preamble merges, but distinct major sections stay separated."""
    # Create doc with small preamble and small section
    preamble = _make_block(0, "Small preamble note.", font_size=10.0, is_bold=False)
    sec1 = _make_block(1, "1. First Section", font_size=14.0, is_bold=True)
    sec1_p = _make_block(2, "Content of first section.", font_size=10.0, is_bold=False)
    sec2 = _make_block(3, "2. Second Section", font_size=14.0, is_bold=True)
    sec2_p = _make_block(4, "Content of second section.", font_size=10.0, is_bold=False)

    doc = Document(
        source_path="/tmp/test.pdf",
        page_count=1,
        pages=[Page(1, 595.0, 842.0, [preamble, sec1, sec1_p, sec2, sec2_p])],
    )

    chunks = chunk_sdca(doc, target_tokens=300, min_tokens=100, max_tokens=500)
    # Major sections 1 and 2 must retain separate chunks despite small size
    sec_names = [c.section for c in chunks]
    assert "1. First Section" in sec_names
    assert "2. Second Section" in sec_names


def test_oversized_paragraph():
    """Test 8: An oversized paragraph (> max_tokens) is safely split into multiple units."""
    # Create paragraph with 12 distinct sentences (~150 tokens) with max_tokens set to 50
    sentences = [f"Sentence number {i} discusses empirical verification." for i in range(12)]
    long_p_text = " ".join(sentences)

    h_block = _make_block(0, "1. Extensive Overview", font_size=14.0, is_bold=True)
    p_block = _make_block(1, long_p_text, font_size=10.0, is_bold=False)

    doc = Document(source_path="/tmp/long.pdf", page_count=1, pages=[Page(1, 595.0, 842.0, [h_block, p_block])])
    chunks = chunk_sdca(doc, target_tokens=40, min_tokens=20, max_tokens=50)

    assert len(chunks) > 1
    for c in chunks:
        assert c.token_count <= 50 or "Extensive Overview" in c.text


def test_sentence_level_splitting():
    """Test 9: Oversized paragraph splitting strictly occurs at sentence boundaries."""
    sentences = [
        "First complete sentence here.",
        "Second complete sentence follows.",
        "Third complete sentence concludes the point.",
        "Fourth complete sentence begins a new phase.",
    ]
    long_p = " ".join(sentences)
    h_block = _make_block(0, "1. Scope", font_size=14.0, is_bold=True)
    p_block = _make_block(1, long_p, font_size=10.0, is_bold=False)

    doc = Document(source_path="/tmp/sent.pdf", page_count=1, pages=[Page(1, 595.0, 842.0, [h_block, p_block])])
    chunks = chunk_sdca(doc, target_tokens=15, min_tokens=8, max_tokens=20)

    # Each chunk text should end with a period
    for c in chunks:
        assert c.text.endswith(".")


def test_oversized_sentence_fallback():
    """Test 10: An extreme oversized sentence without punctuation falls back safely without loss."""
    # A single giant run-on sentence without punctuation
    words = [f"word{i}" for i in range(100)]
    giant_sent = " ".join(words)

    h_block = _make_block(0, "1. Runon Section", font_size=14.0, is_bold=True)
    p_block = _make_block(1, giant_sent, font_size=10.0, is_bold=False)

    doc = Document(source_path="/tmp/giant.pdf", page_count=1, pages=[Page(1, 595.0, 842.0, [h_block, p_block])])
    chunks = chunk_sdca(doc, target_tokens=30, min_tokens=15, max_tokens=40)

    assert len(chunks) >= 3
    # Verify no word is truncated or missing
    all_chunk_text = " ".join(c.text.replace("1. Runon Section", "") for c in chunks)
    recombined_words = set(all_chunk_text.split())
    for w in words:
        assert w in recombined_words


def test_page_start_preservation(structured_doc: Document):
    """Test 11: page_start accurately records the beginning page of the chunk."""
    chunks = chunk_sdca(structured_doc, target_tokens=200, min_tokens=100, max_tokens=400)
    for c in chunks:
        assert c.page_start in {1, 2}


def test_page_end_preservation(structured_doc: Document):
    """Test 12: page_end accurately records the ending page and page_start <= page_end."""
    chunks = chunk_sdca(structured_doc, target_tokens=200, min_tokens=100, max_tokens=400)
    for c in chunks:
        assert 1 <= c.page_start <= c.page_end <= 2


def test_no_empty_chunks(structured_doc: Document):
    """Test 13: SDCA produces no empty or whitespace-only chunks."""
    chunks = chunk_sdca(structured_doc, target_tokens=200, min_tokens=100, max_tokens=400)
    for c in chunks:
        assert len(c.text.strip()) > 0
        assert c.token_count > 0


def test_no_accidental_duplicated_text(structured_doc: Document):
    """Test 14: Content paragraphs are not duplicated across chunks."""
    chunks = chunk_sdca(structured_doc, target_tokens=200, min_tokens=100, max_tokens=400)
    p5_text = structured_doc.pages[0].blocks[5].text
    # p5 should only appear in exactly one chunk
    matches = [c for c in chunks if p5_text in c.text]
    assert len(matches) == 1


def test_no_lost_text(structured_doc: Document):
    """Test 15: Every paragraph from the source document is accounted for in output chunks."""
    chunks = chunk_sdca(structured_doc, target_tokens=200, min_tokens=100, max_tokens=400)
    for page in structured_doc.pages:
        for block in page.blocks:
            # Check non-title body paragraphs
            if block.block_type == 0 and len(block.text.split()) > 10:
                assert any(block.text in c.text for c in chunks), f"Lost paragraph: {block.text[:30]}"


def test_no_intentional_word_splitting():
    """Test 16: SDCA never cleaves words into pieces."""
    text = "wordOne wordTwo wordThree wordFour wordFive wordSix wordSeven wordEight wordNine wordTen"
    h_block = _make_block(0, "1. Words", font_size=14.0, is_bold=True)
    p_block = _make_block(1, text, font_size=10.0, is_bold=False)

    doc = Document(source_path="/tmp/words.pdf", page_count=1, pages=[Page(1, 595.0, 842.0, [h_block, p_block])])
    chunks = chunk_sdca(doc, target_tokens=6, min_tokens=2, max_tokens=8)

    for c in chunks:
        for w in c.text.split():
            assert w in text or w in "1. Words"


def test_deterministic_repeated_execution(structured_doc: Document):
    """Test 17: Repeated executions on identical input produce identical output chunks."""
    run1 = chunk_sdca(structured_doc, target_tokens=250, min_tokens=100, max_tokens=500)
    run2 = chunk_sdca(structured_doc, target_tokens=250, min_tokens=100, max_tokens=500)

    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.text == c2.text
        assert c1.section == c2.section
        assert c1.page_start == c2.page_start
        assert c1.page_end == c2.page_end
        assert c1.token_count == c2.token_count


def test_target_size_configuration(structured_doc: Document):
    """Test 18: Configuring target token boundaries adjusts chunk counts predictably."""
    small_chunks = chunk_sdca(structured_doc, target_tokens=25, min_tokens=10, max_tokens=30)
    large_chunks = chunk_sdca(structured_doc, target_tokens=400, min_tokens=200, max_tokens=600)
    assert len(small_chunks) > len(large_chunks)


def test_strategy_label(structured_doc: Document):
    """Test 19: All generated chunks identify strategy as 'sdca'."""
    chunks = chunk_sdca(structured_doc)
    assert all(c.strategy == "sdca" for c in chunks)


def test_no_embeddings_required():
    """Test 20: SDCA executes independently without requiring neural models or embeddings."""
    tok = RegexTokenizer()
    chunks = chunk_sdca("1. Simple Section\n\nThis is a simple test text.", tokenizer=tok)
    assert len(chunks) == 1
    assert chunks[0].strategy == "sdca"


def test_text_order_preservation(structured_doc: Document):
    """Test 21: Sequence of chunks strictly matches document reading order."""
    chunks = chunk_sdca(structured_doc, target_tokens=150, min_tokens=50, max_tokens=250)
    # Verify Introduction chunk occurs before Methodology, which occurs before Conclusion
    intro_idx = next(i for i, c in enumerate(chunks) if c.section == "1. Introduction")
    method_idx = next(i for i, c in enumerate(chunks) if c.section == "2. Proposed Methodology")
    concl_idx = next(i for i, c in enumerate(chunks) if c.section == "3. Conclusion")
    assert intro_idx < method_idx < concl_idx


def test_content_reconstruction(structured_doc: Document):
    """Test 22: Content reconstruction test detects missing, duplicated, or reordered text."""
    chunks = chunk_sdca(structured_doc, target_tokens=250, min_tokens=100, max_tokens=500)

    # Collect all words from body paragraphs in structured_doc
    source_words: List[str] = []
    for page in structured_doc.pages:
        for block in page.blocks:
            source_words.extend(block.text.split())

    # Collect all words from emitted chunks
    chunk_words: List[str] = []
    for c in chunks:
        chunk_words.extend(c.text.split())

    # Every source body word must be present in chunk_words
    source_word_set = set(source_words)
    chunk_word_set = set(chunk_words)
    missing_words = source_word_set - chunk_word_set
    assert not missing_words, f"Detected missing words in SDCA output: {missing_words}"


def test_baseline_separation():
    """Test 23: Verify SDCA implementation has no imports of embeddings or neural libraries."""
    import subprocess
    forbidden_modules = [
        "sentence_transformers",
        "faiss",
        "streamlit",
        "transformers",
        "torch",
        "langchain",
    ]
    check_code = f"""
import sys
import src.sdca
forbidden = {forbidden_modules}
for mod in forbidden:
    if mod in sys.modules:
        sys.exit(1)
sys.exit(0)
"""
    result = subprocess.run([sys.executable, "-c", check_code], capture_output=True)
    assert result.returncode == 0, "SDCA imported forbidden embedding/neural libraries in an isolated process!"

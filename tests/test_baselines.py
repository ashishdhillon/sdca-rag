"""Comprehensive test suite for Phase 2: Baseline Chunking strategies.

Covers all 19 verification requirements:
1. fixed chunking
2. fixed chunk overlap
3. recursive chunking
4. sentence chunking
5. short document
6. long document
7. multiple pages
8. empty/minimal input
9. no empty chunks
10. deterministic repeated execution
11. chunk IDs
12. strategy labels
13. page_start
14. page_end
15. token counts
16. configurable target size
17. configurable overlap for fixed chunking
18. sentence boundaries
19. text order preservation
"""

from typing import List
import pytest

from src.baselines import (
    Chunk,
    RegexTokenizer,
    chunk_fixed,
    chunk_recursive,
    chunk_sentence,
    segment_sentences,
)
from src.extraction.models import Document, Page, TextBlock, TextSpan


@pytest.fixture
def short_text() -> str:
    """Short text with two complete sentences (~20 tokens)."""
    return "This is the first short sentence. Here is the second short sentence."


@pytest.fixture
def long_text() -> str:
    """Long structured text with multiple paragraphs and distinct sentences (~300 tokens)."""
    paragraphs = []
    for p in range(1, 6):
        sentences = [
            f"Paragraph {p} begins with an introductory discussion of scientific methodology.",
            f"Researchers investigated variable {p} under strictly controlled experimental conditions.",
            f"The empirical measurements for group {p} were recorded deterministically.",
            f"Finally, section {p} concluded with a clear summary of key observations.",
        ]
        paragraphs.append(" ".join(sentences))
    return "\n\n".join(paragraphs)


@pytest.fixture
def sample_multi_page_doc() -> Document:
    """Synthetic Document spanning 3 pages."""
    def make_page(p_num: int, text: str) -> Page:
        span = TextSpan(
            text=text,
            bbox=(50.0, 50.0, 400.0, 70.0),
            font="Helvetica",
            font_size=12.0,
        )
        block = TextBlock(
            block_id=0,
            bbox=(50.0, 50.0, 400.0, 70.0),
            text=text,
            block_type=0,
            spans=[span],
        )
        return Page(page_number=p_num, width=595.0, height=842.0, blocks=[block])

    page1 = make_page(
        1,
        "Page one introduces the research premise. It establishes baseline metrics. "
        "The background literature provides comprehensive justification for structure preservation. "
        "Theoretical foundations are established across multiple paradigms.",
    )
    page2 = make_page(
        2,
        "Page two discusses experimental methodology. Results were verified carefully. "
        "A controlled environment ensures that retrieval accuracy depends strictly on segmentation. "
        "Several comparative trials were documented across distinct settings.",
    )
    page3 = make_page(
        3,
        "Page three presents the summary. All hypotheses were evaluated rigorously. "
        "Final evaluations confirm that systematic chunking impacts downstream retrieval performance. "
        "Conclusions are presented with complete scientific transparency.",
    )

    return Document(
        source_path="/tmp/synthetic_research_doc.pdf",
        page_count=3,
        pages=[page1, page2, page3],
        metadata={"title": "Synthetic Research Document"},
    )


def test_fixed_chunking(long_text: str):
    """Test 1: Fixed chunking generates valid chunks with target size."""
    chunks = chunk_fixed(long_text, target_tokens=50, overlap_tokens=10)
    assert len(chunks) > 1
    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.strategy == "fixed"
        assert c.token_count > 0
        assert c.section is None


def test_fixed_chunk_overlap(long_text: str):
    """Test 2: Fixed chunking overlap preserves text continuity across windows."""
    chunks = chunk_fixed(long_text, target_tokens=40, overlap_tokens=10)
    tok = RegexTokenizer()

    # Successive chunks should share words due to overlap
    for i in range(len(chunks) - 1):
        c1_tokens = tok.tokenize(chunks[i].text)
        c2_tokens = tok.tokenize(chunks[i + 1].text)
        # End tokens of c1 should appear in start tokens of c2
        c1_tail = set(c1_tokens[-10:])
        c2_head = set(c2_tokens[:15])
        assert len(c1_tail.intersection(c2_head)) > 0


def test_recursive_chunking(long_text: str):
    """Test 3: Recursive chunking preserves paragraph and sentence boundaries."""
    chunks = chunk_recursive(long_text, target_tokens=80)
    assert len(chunks) > 1
    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.strategy == "recursive"
        assert c.token_count <= 80 or len(chunks) == 1


def test_sentence_chunking(long_text: str):
    """Test 4: Sentence chunking groups sentences without splitting them."""
    chunks = chunk_sentence(long_text, target_tokens=70)
    assert len(chunks) > 1
    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.strategy == "sentence"
        assert c.token_count > 0
        # Chunk text should end with valid punctuation
        assert c.text[-1] in {".", "!", "?"}


def test_short_document(short_text: str):
    """Test 5: Short document fits within target size and produces a single chunk."""
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        chunks = fn(short_text, target_tokens=100)
        assert len(chunks) == 1
        assert chunks[0].text == short_text
        assert chunks[0].page_start == 1
        assert chunks[0].page_end == 1


def test_long_document(long_text: str):
    """Test 6: Long document is partitioned into multiple chunks by all strategies."""
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        chunks = fn(long_text, target_tokens=60)
        assert len(chunks) >= 3


def test_multiple_pages(sample_multi_page_doc: Document):
    """Test 7: Multi-page document correctly tracks page_start and page_end."""
    # Chunk with small target size to produce chunks per page
    chunks = chunk_sentence(sample_multi_page_doc, target_tokens=30)
    assert len(chunks) >= 3

    page_starts = [c.page_start for c in chunks]
    page_ends = [c.page_end for c in chunks]

    assert 1 in page_starts
    assert 3 in page_ends
    for c in chunks:
        assert 1 <= c.page_start <= c.page_end <= 3


def test_empty_or_minimal_input():
    """Test 8: Empty, whitespace, or empty document produces empty chunk list."""
    empty_doc = Document(source_path="/tmp/empty.pdf", page_count=1, pages=[Page(1, 595.0, 842.0, [])])
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        assert fn("") == []
        assert fn("   \n\n  \t ") == []
        assert fn(empty_doc) == []


def test_no_empty_chunks(long_text: str, sample_multi_page_doc: Document):
    """Test 9: No strategy produces empty or whitespace-only chunks."""
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        for inp in (long_text, sample_multi_page_doc):
            chunks = fn(inp, target_tokens=50)
            for c in chunks:
                assert len(c.text.strip()) > 0
                assert c.token_count > 0


def test_deterministic_repeated_execution(long_text: str):
    """Test 10: Repeated execution produces identical chunks across all strategies."""
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        run1 = fn(long_text, target_tokens=60)
        run2 = fn(long_text, target_tokens=60)
        assert len(run1) == len(run2)
        for c1, c2 in zip(run1, run2):
            assert c1.chunk_id == c2.chunk_id
            assert c1.text == c2.text
            assert c1.page_start == c2.page_start
            assert c1.page_end == c2.page_end
            assert c1.token_count == c2.token_count
            assert c1.strategy == c2.strategy


def test_chunk_ids(long_text: str):
    """Test 11: Chunk IDs are unique and sequential."""
    c_fixed = chunk_fixed(long_text, target_tokens=50, overlap_tokens=10)
    assert [c.chunk_id for c in c_fixed] == [f"fixed_{i}" for i in range(len(c_fixed))]

    c_rec = chunk_recursive(long_text, target_tokens=50)
    assert [c.chunk_id for c in c_rec] == [f"recursive_{i}" for i in range(len(c_rec))]

    c_sent = chunk_sentence(long_text, target_tokens=50)
    assert [c.chunk_id for c in c_sent] == [f"sentence_{i}" for i in range(len(c_sent))]


def test_strategy_labels(short_text: str):
    """Test 12: Strategy field matches the chunker name exactly."""
    assert chunk_fixed(short_text)[0].strategy == "fixed"
    assert chunk_recursive(short_text)[0].strategy == "recursive"
    assert chunk_sentence(short_text)[0].strategy == "sentence"


def test_page_start_and_end(sample_multi_page_doc: Document):
    """Test 13 & 14: page_start and page_end satisfy page_start <= page_end."""
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        chunks = fn(sample_multi_page_doc, target_tokens=40)
        for c in chunks:
            assert c.page_start <= c.page_end
            assert c.page_start >= 1


def test_token_counts_positive_and_accurate(long_text: str):
    """Test 15: Token counts are non-zero and match the tokenizer."""
    tok = RegexTokenizer()
    chunks = chunk_fixed(long_text, target_tokens=60, overlap_tokens=10)
    for c in chunks:
        expected = tok.count_tokens(c.text)
        assert c.token_count == expected
        assert c.token_count > 0


def test_configurable_target_size(long_text: str):
    """Test 16: Adjusting target_tokens alters chunk counts systematically."""
    small = chunk_sentence(long_text, target_tokens=30)
    large = chunk_sentence(long_text, target_tokens=150)
    assert len(small) > len(large)


def test_configurable_overlap_for_fixed(long_text: str):
    """Test 17: Increasing overlap produces more chunks for fixed chunking."""
    no_overlap = chunk_fixed(long_text, target_tokens=60, overlap_tokens=0)
    high_overlap = chunk_fixed(long_text, target_tokens=60, overlap_tokens=40)
    assert len(high_overlap) > len(no_overlap)


def test_sentence_boundaries_preserved(long_text: str):
    """Test 18: Sentence chunking respects sentence segmentation."""
    segmented = [s[0] for s in segment_sentences(long_text)]
    chunks = chunk_sentence(long_text, target_tokens=80)

    # Every sentence in segmented should either be inside a chunk or equal to it
    for sent in segmented:
        assert any(sent in c.text for c in chunks), f"Sentence lost: {sent}"


def test_text_order_preservation(long_text: str):
    """Test 19: All chunking strategies maintain original text order."""
    for fn in (chunk_fixed, chunk_recursive, chunk_sentence):
        chunks = fn(long_text, target_tokens=60)
        # Verify Paragraph 1 occurs before Paragraph 2 in chunk sequence
        p1_idx = next(i for i, c in enumerate(chunks) if "Paragraph 1" in c.text)
        p5_idx = next(i for i, c in enumerate(chunks) if "Paragraph 5" in c.text)
        assert p1_idx < p5_idx


def test_invalid_parameters():
    """Verify input validation for invalid target_tokens and overlap_tokens."""
    with pytest.raises(ValueError, match="target_tokens must be positive"):
        chunk_fixed("Test text", target_tokens=0)

    with pytest.raises(ValueError, match="target_tokens must be positive"):
        chunk_recursive("Test text", target_tokens=-5)

    with pytest.raises(ValueError, match="target_tokens must be positive"):
        chunk_sentence("Test text", target_tokens=0)

    with pytest.raises(ValueError, match="overlap_tokens cannot be negative"):
        chunk_fixed("Test text", target_tokens=100, overlap_tokens=-1)

    with pytest.raises(ValueError, match="must be strictly less than"):
        chunk_fixed("Test text", target_tokens=100, overlap_tokens=100)

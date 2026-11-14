"""Unit tests for SDCA V2 (Structure-Aware Document Chunking Algorithm V2).

Verifies the 4 core improvements:
1. Heading-content binding (no standalone heading-only chunks)
2. Hierarchical section context and ancestral paths
3. Structure-aware retrieval representations
4. Adaptive small-chunk merging within hierarchy
"""

import pytest

from src.baselines.models import Chunk
from src.baselines.tokenization import RegexTokenizer
from src.extraction.models import Document, Page, TextBlock, TextSpan
from src.sdca.chunker import chunk_sdca
from src.sdca.v2.chunker import chunk_sdca_v2
from src.sdca.v2.structure import (
    HeadingDetectorV2,
    HeadingNode,
    SectionV2,
    detect_document_structure_v2,
)


def make_hierarchical_document() -> Document:
    """Creates a synthetic multi-page document with a rich section hierarchy."""
    blocks: List[TextBlock] = []

    # Block 0: Preamble
    s0 = TextSpan(text="This is an introductory preamble.", bbox=(50.0, 50.0, 400.0, 70.0), font="Helvetica", font_size=10.0, flags=0)
    blocks.append(TextBlock(block_id=0, bbox=s0.bbox, text=s0.text, block_type=0, spans=[s0]))

    # Block 1: Level 1 Heading (3. Model Architecture) - Umbrella heading with NO body text
    s1 = TextSpan(text="3. Model Architecture", bbox=(50.0, 100.0, 400.0, 125.0), font="Helvetica-Bold", font_size=14.0, flags=4)
    blocks.append(TextBlock(block_id=1, bbox=s1.bbox, text=s1.text, block_type=0, spans=[s1]))

    # Block 2: Level 2 Heading (3.1 Encoder and Decoder Stacks)
    s2 = TextSpan(text="3.1 Encoder and Decoder Stacks", bbox=(50.0, 150.0, 400.0, 172.0), font="Helvetica-Bold", font_size=12.0, flags=4)
    blocks.append(TextBlock(block_id=2, bbox=s2.bbox, text=s2.text, block_type=0, spans=[s2]))

    # Block 3: Body paragraph for 3.1
    s3 = TextSpan(
        text="The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers.",
        bbox=(50.0, 190.0, 400.0, 220.0), font="Helvetica", font_size=10.0, flags=0
    )
    blocks.append(TextBlock(block_id=3, bbox=s3.bbox, text=s3.text, block_type=0, spans=[s3]))

    # Block 4: Level 2 Heading (3.2 Attention)
    s4 = TextSpan(text="3.2 Attention", bbox=(50.0, 240.0, 400.0, 262.0), font="Helvetica-Bold", font_size=12.0, flags=4)
    blocks.append(TextBlock(block_id=4, bbox=s4.bbox, text=s4.text, block_type=0, spans=[s4]))

    # Block 5: Level 3 Heading (3.2.1 Scaled Dot-Product Attention)
    s5 = TextSpan(text="3.2.1 Scaled Dot-Product Attention", bbox=(50.0, 280.0, 400.0, 300.0), font="Helvetica-Bold", font_size=11.0, flags=4)
    blocks.append(TextBlock(block_id=5, bbox=s5.bbox, text=s5.text, block_type=0, spans=[s5]))

    # Block 6: Body paragraph for 3.2.1
    s6 = TextSpan(
        text="We call our particular attention Scaled Dot-Product Attention. The input consists of queries and keys of dimension d_k.",
        bbox=(50.0, 310.0, 400.0, 350.0), font="Helvetica", font_size=10.0, flags=0
    )
    blocks.append(TextBlock(block_id=6, bbox=s6.bbox, text=s6.text, block_type=0, spans=[s6]))

    # Block 7: Level 1 Heading (4. Conclusion)
    s7 = TextSpan(text="4. Conclusion", bbox=(50.0, 380.0, 400.0, 405.0), font="Helvetica-Bold", font_size=14.0, flags=4)
    blocks.append(TextBlock(block_id=7, bbox=s7.bbox, text=s7.text, block_type=0, spans=[s7]))

    # Block 8: Body paragraph for Conclusion
    s8 = TextSpan(
        text="In this work, we presented the Transformer, the first sequence transduction model based entirely on attention.",
        bbox=(50.0, 420.0, 400.0, 460.0), font="Helvetica", font_size=10.0, flags=0
    )
    blocks.append(TextBlock(block_id=8, bbox=s8.bbox, text=s8.text, block_type=0, spans=[s8]))

    page = Page(page_number=1, width=595.0, height=842.0, blocks=blocks)
    return Document(source_path="<test-hierarchical-doc>", page_count=1, pages=[page])


def test_heading_detector_v2_levels():
    body_size = 10.0
    page = Page(page_number=1, width=595.0, height=842.0, blocks=[])

    # Level 1 Numbered
    s1 = TextSpan(text="1. Introduction", bbox=(50.0, 100.0, 400.0, 120.0), font="Helvetica-Bold", font_size=14.0, flags=4)
    b1 = TextBlock(block_id=0, bbox=s1.bbox, text=s1.text, block_type=0, spans=[s1])
    is_hd, title, lvl = HeadingDetectorV2.is_heading(b1, body_size, page)
    assert is_hd is True
    assert lvl == 1

    # Level 2 Numbered
    s2 = TextSpan(text="3.2 Attention", bbox=(50.0, 100.0, 400.0, 120.0), font="Helvetica-Bold", font_size=12.0, flags=4)
    b2 = TextBlock(block_id=1, bbox=s2.bbox, text=s2.text, block_type=0, spans=[s2])
    is_hd, title, lvl = HeadingDetectorV2.is_heading(b2, body_size, page)
    assert is_hd is True
    assert lvl == 2

    # Level 3 Numbered
    s3 = TextSpan(text="3.2.1 Scaled Dot-Product Attention", bbox=(50.0, 100.0, 400.0, 120.0), font="Helvetica-Bold", font_size=11.0, flags=4)
    b3 = TextBlock(block_id=2, bbox=s3.bbox, text=s3.text, block_type=0, spans=[s3])
    is_hd, title, lvl = HeadingDetectorV2.is_heading(b3, body_size, page)
    assert is_hd is True
    assert lvl == 3

    # Canonical title -> Level 1
    s4 = TextSpan(text="Abstract", bbox=(50.0, 100.0, 400.0, 120.0), font="Helvetica-Bold", font_size=12.0, flags=4)
    b4 = TextBlock(block_id=3, bbox=s4.bbox, text=s4.text, block_type=0, spans=[s4])
    is_hd, title, lvl = HeadingDetectorV2.is_heading(b4, body_size, page)
    assert is_hd is True
    assert lvl == 1


def test_detect_document_structure_v2_hierarchy():
    doc = make_hierarchical_document()
    sections = detect_document_structure_v2(doc)

    assert len(sections) >= 3

    # Verify that '3. Model Architecture' was absorbed as an umbrella parent
    # and did NOT create an empty section with 0 paragraphs
    for sec in sections:
        assert len(sec.paragraphs) > 0

    # Find section for 3.1
    sec_31 = next(s for s in sections if s.heading == "3.1 Encoder and Decoder Stacks")
    assert sec_31.parent_heading == "3. Model Architecture"
    assert "3. Model Architecture" in sec_31.section_path
    assert sec_31.section_path_str == "3. Model Architecture > 3.1 Encoder and Decoder Stacks"

    # Find section for 3.2.1
    sec_321 = next(s for s in sections if s.heading == "3.2.1 Scaled Dot-Product Attention")
    assert "3. Model Architecture" in sec_321.section_path
    assert "3.2 Attention" in sec_321.section_path
    assert sec_321.section_path_str == "3. Model Architecture > 3.2 Attention > 3.2.1 Scaled Dot-Product Attention"


def test_sdca_v2_no_standalone_heading_chunks():
    doc = make_hierarchical_document()
    chunks = chunk_sdca_v2(doc, min_tokens=50, target_tokens=400, max_tokens=600)

    assert len(chunks) > 0

    # Ensure no chunk consists strictly of an isolated heading title
    for c in chunks:
        assert c.token_count >= 10
        # If it has a heading, it must also have body content
        if c.section:
            lines = c.text.strip().split("\n\n")
            assert len(lines) >= 2, f"Chunk {c.chunk_id} appears to be heading-only: {c.text}"


def test_sdca_v2_structure_aware_retrieval_text():
    doc = make_hierarchical_document()
    chunks = chunk_sdca_v2(doc, min_tokens=50, target_tokens=400, max_tokens=600)

    for c in chunks:
        # Every chunk must have retrieval_text populated
        assert c.retrieval_text is not None
        assert "retrieval_text" in c.metadata

        # For structured sections, retrieval text must contain the ancestral breadcrumb
        if c.section and c.section != "4. Conclusion":
            assert "[Section:" in c.retrieval_text
            assert "3. Model Architecture" in c.retrieval_text

            # Clean display text should NOT have the bracketed prefix
            assert not c.text.startswith("[Section:")


def test_sdca_v2_hierarchical_metadata():
    doc = make_hierarchical_document()
    chunks = chunk_sdca_v2(doc, min_tokens=50, target_tokens=400, max_tokens=600)

    # Find chunk belonging to attention subsection
    att_chunk = next(c for c in chunks if "Scaled Dot-Product Attention" in c.text)
    assert att_chunk.section == "3.2.1 Scaled Dot-Product Attention"
    assert att_chunk.metadata["parent_heading"] == "3.2 Attention"
    assert att_chunk.metadata["section_path_str"] == "3. Model Architecture > 3.2 Attention > 3.2.1 Scaled Dot-Product Attention"
    assert att_chunk.strategy == "sdca_v2"


def test_sdca_v2_small_chunk_merging_respects_major_boundaries():
    # Synthetic doc with 2 small sections: one subsection, and Conclusion
    doc = make_hierarchical_document()
    tok = RegexTokenizer()

    # With higher min_tokens, compatible subsections can merge, but Conclusion must NOT merge with Architecture
    chunks = chunk_sdca_v2(doc, target_tokens=400, min_tokens=200, max_tokens=600, tokenizer=tok)

    # Conclusion must remain structurally separate from Section 3
    conclusion_chunk = next(c for c in chunks if "4. Conclusion" in c.text)
    assert "3. Model Architecture" not in conclusion_chunk.text
    assert conclusion_chunk.section == "4. Conclusion"


def test_v1_and_v2_coexist_independently():
    doc = make_hierarchical_document()
    tok = RegexTokenizer()

    chunks_v1 = chunk_sdca(doc, target_tokens=400, min_tokens=200, max_tokens=600, tokenizer=tok)
    chunks_v2 = chunk_sdca_v2(doc, target_tokens=400, min_tokens=200, max_tokens=600, tokenizer=tok)

    assert len(chunks_v1) > 0
    assert len(chunks_v2) > 0

    assert chunks_v1[0].strategy == "sdca"
    assert chunks_v2[0].strategy == "sdca_v2"

    # V2 has retrieval_text, V1 does not
    assert chunks_v2[0].retrieval_text is not None


def test_sdca_v2_deterministic_execution():
    doc = make_hierarchical_document()
    tok = RegexTokenizer()

    run1 = chunk_sdca_v2(doc, tokenizer=tok)
    run2 = chunk_sdca_v2(doc, tokenizer=tok)

    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.text == c2.text
        assert c1.retrieval_text == c2.retrieval_text
        assert c1.token_count == c2.token_count
        assert c1.metadata == c2.metadata


def test_sdca_v2_invalid_parameters():
    doc = make_hierarchical_document()

    with pytest.raises(ValueError, match="min_tokens must be positive"):
        chunk_sdca_v2(doc, min_tokens=0)

    with pytest.raises(ValueError, match="target_tokens .* must be >= min_tokens"):
        chunk_sdca_v2(doc, target_tokens=150, min_tokens=200)

    with pytest.raises(ValueError, match="max_tokens .* must be >= target_tokens"):
        chunk_sdca_v2(doc, target_tokens=500, max_tokens=400)

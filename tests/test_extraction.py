"""Unit test suite for Phase 1: PDF Extraction Foundation.

Covers all 15 required verification targets:
1. Valid single-page PDF
2. Valid multi-page PDF
3. Page numbering (1-based)
4. Page ordering
5. Text extraction
6. Multiple text blocks
7. Span extraction
8. Font size extraction
9. Font metadata extraction
10. Bounding box extraction
11. Page dimensions
12. Empty/minimal page
13. Missing PDF
14. Invalid PDF
15. Deterministic repeated extraction
"""

from pathlib import Path
import pytest
import pymupdf

from src.extraction import Document, Page, TextBlock, TextSpan, load_pdf


@pytest.fixture
def single_page_pdf(tmp_path: Path) -> Path:
    """Creates a temporary single-page PDF with a title and paragraph."""
    pdf_path = tmp_path / "single_page.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.0, height=842.0)  # A4 size

    # Insert title with 18pt Helvetica
    page.insert_text((50, 100), "Title of Research Document", fontsize=18.0, fontname="helv")
    # Insert paragraph with 11pt Helvetica
    page.insert_text(
        (50, 180),
        "This is a sample paragraph explaining the extraction foundation.",
        fontsize=11.0,
        fontname="helv",
    )

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    """Creates a temporary 3-page PDF with distinct content and an empty page."""
    pdf_path = tmp_path / "multi_page.pdf"
    doc = pymupdf.open()

    # Page 1: A4 (595 x 842)
    page1 = doc.new_page(width=595.0, height=842.0)
    page1.insert_text((50, 100), "Chapter 1: Background", fontsize=16.0, fontname="helv")
    page1.insert_text((50, 150), "Content of chapter one.", fontsize=10.0, fontname="helv")

    # Page 2: Letter (612 x 792)
    page2 = doc.new_page(width=612.0, height=792.0)
    page2.insert_text((60, 120), "Chapter 2: Methodology", fontsize=14.0, fontname="times-roman")
    page2.insert_text((60, 170), "Content of chapter two.", fontsize=10.0, fontname="times-roman")

    # Page 3: A4, empty page
    doc.new_page(width=595.0, height=842.0)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_valid_single_page_pdf(single_page_pdf: Path):
    """Test 1: Valid single-page PDF loads correctly into Document model."""
    doc = load_pdf(single_page_pdf)
    assert isinstance(doc, Document)
    assert doc.page_count == 1
    assert len(doc.pages) == 1
    assert Path(doc.source_path) == single_page_pdf.resolve()


def test_valid_multi_page_pdf(multi_page_pdf: Path):
    """Test 2: Valid multi-page PDF loads correct number of pages."""
    doc = load_pdf(multi_page_pdf)
    assert isinstance(doc, Document)
    assert doc.page_count == 3
    assert len(doc.pages) == 3


def test_page_numbering_one_based(multi_page_pdf: Path):
    """Test 3: Page numbering strictly follows 1-based convention."""
    doc = load_pdf(multi_page_pdf)
    page_numbers = [p.page_number for p in doc.pages]
    assert page_numbers == [1, 2, 3]


def test_page_ordering(multi_page_pdf: Path):
    """Test 4: Pages are extracted strictly in physical sequential order."""
    doc = load_pdf(multi_page_pdf)
    assert "Chapter 1" in doc.pages[0].text
    assert "Chapter 2" in doc.pages[1].text
    assert doc.pages[2].text == ""


def test_text_extraction(single_page_pdf: Path):
    """Test 5: Text content is accurately preserved and accessible."""
    doc = load_pdf(single_page_pdf)
    page = doc.pages[0]
    assert "Title of Research Document" in page.text
    assert "This is a sample paragraph" in page.text
    assert "Title of Research Document" in doc.text


def test_multiple_text_blocks(single_page_pdf: Path):
    """Test 6: Distinct text blocks are extracted with sequential block_ids."""
    doc = load_pdf(single_page_pdf)
    page = doc.pages[0]
    text_blocks = page.text_blocks
    assert len(text_blocks) >= 2
    for b in text_blocks:
        assert isinstance(b, TextBlock)
        assert b.block_type == 0
        assert b.block_id >= 0


def test_span_extraction(single_page_pdf: Path):
    """Test 7: Each text block preserves internal styling spans."""
    doc = load_pdf(single_page_pdf)
    block = doc.pages[0].text_blocks[0]
    assert len(block.spans) >= 1
    span = block.spans[0]
    assert isinstance(span, TextSpan)
    assert "Title of Research Document" in span.text


def test_font_size_extraction(single_page_pdf: Path):
    """Test 8: Font size in points is correctly captured across spans."""
    doc = load_pdf(single_page_pdf)
    blocks = doc.pages[0].text_blocks

    title_span = blocks[0].spans[0]
    body_span = blocks[1].spans[0]

    # Title was inserted with fontsize=18, body with fontsize=11
    assert pytest.approx(title_span.font_size, rel=0.1) == 18.0
    assert pytest.approx(body_span.font_size, rel=0.1) == 11.0
    assert title_span.font_size > body_span.font_size


def test_font_metadata_extraction(multi_page_pdf: Path):
    """Test 9: Font name identifier and flags are preserved."""
    doc = load_pdf(multi_page_pdf)

    # Page 1 used helv (Helvetica)
    span_p1 = doc.pages[0].text_blocks[0].spans[0]
    assert "helv" in span_p1.font.lower()
    assert isinstance(span_p1.flags, int)

    # Page 2 used times-roman
    span_p2 = doc.pages[1].text_blocks[0].spans[0]
    assert "times" in span_p2.font.lower()
    assert isinstance(span_p2.flags, int)


def test_bounding_box_extraction(single_page_pdf: Path):
    """Test 10: Bounding boxes are well-formed coordinates (x0 < x1, y0 < y1)."""
    doc = load_pdf(single_page_pdf)
    for page in doc.pages:
        for block in page.blocks:
            x0, y0, x1, y1 = block.bbox
            assert x0 < x1, f"Invalid block x-bounds: {block.bbox}"
            assert y0 < y1, f"Invalid block y-bounds: {block.bbox}"
            for span in block.spans:
                sx0, sy0, sx1, sy1 = span.bbox
                assert sx0 < sx1, f"Invalid span x-bounds: {span.bbox}"
                assert sy0 < sy1, f"Invalid span y-bounds: {span.bbox}"


def test_page_dimensions(multi_page_pdf: Path):
    """Test 11: Page width and height are preserved accurately."""
    doc = load_pdf(multi_page_pdf)

    page1 = doc.pages[0]
    assert pytest.approx(page1.width, rel=1e-2) == 595.0
    assert pytest.approx(page1.height, rel=1e-2) == 842.0

    page2 = doc.pages[1]
    assert pytest.approx(page2.width, rel=1e-2) == 612.0
    assert pytest.approx(page2.height, rel=1e-2) == 792.0


def test_empty_or_minimal_page(multi_page_pdf: Path):
    """Test 12: Empty or minimal pages are handled without errors."""
    doc = load_pdf(multi_page_pdf)
    empty_page = doc.pages[2]
    assert empty_page.page_number == 3
    assert len(empty_page.blocks) == 0
    assert empty_page.text == ""
    assert len(empty_page.text_blocks) == 0


def test_missing_pdf(tmp_path: Path):
    """Test 13: Non-existent PDF file raises FileNotFoundError."""
    missing_path = tmp_path / "does_not_exist.pdf"
    with pytest.raises(FileNotFoundError, match="PDF file does not exist"):
        load_pdf(missing_path)


def test_invalid_pdf(tmp_path: Path):
    """Test 14: Invalid or corrupt PDF file raises ValueError."""
    corrupt_file = tmp_path / "corrupt.pdf"
    corrupt_file.write_bytes(b"This is not a PDF file content.")
    with pytest.raises(ValueError, match="Failed to open PDF file"):
        load_pdf(corrupt_file)


def test_deterministic_repeated_extraction(multi_page_pdf: Path):
    """Test 15: Repeated extraction of the same PDF produces identical results."""
    run1 = load_pdf(multi_page_pdf)
    run2 = load_pdf(multi_page_pdf)

    assert run1.page_count == run2.page_count
    for p1, p2 in zip(run1.pages, run2.pages):
        assert p1.page_number == p2.page_number
        assert p1.width == p2.width
        assert p1.height == p2.height
        assert len(p1.blocks) == len(p2.blocks)
        for b1, b2 in zip(p1.blocks, p2.blocks):
            assert b1.block_id == b2.block_id
            assert b1.bbox == b2.bbox
            assert b1.text == b2.text
            assert len(b1.spans) == len(b2.spans)
            for s1, s2 in zip(b1.spans, b2.spans):
                assert s1.text == s2.text
                assert s1.bbox == s2.bbox
                assert s1.font == s2.font
                assert s1.font_size == s2.font_size
                assert s1.flags == s2.flags

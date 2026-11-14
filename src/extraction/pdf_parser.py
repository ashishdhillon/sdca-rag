"""PDF parser implementation using PyMuPDF (fitz).

This module provides deterministic extraction of document structure,
preserving page geometry, text blocks, spans, font typography, and bounding boxes.
No chunking, heading detection, or neural semantic processing is performed here.
"""

from pathlib import Path
from typing import Any, Dict, List, Union

import pymupdf

from src.extraction.models import Document, Page, TextBlock, TextSpan


def extract_blocks(page_dict: Dict[str, Any]) -> List[TextBlock]:
    """Extracts structured TextBlock instances from a PyMuPDF page dictionary.

    Args:
        page_dict: Dictionary returned by PyMuPDF's page.get_text("dict").

    Returns:
        List of TextBlock objects preserving reading order and styling spans.
    """
    blocks: List[TextBlock] = []
    raw_blocks = page_dict.get("blocks", [])

    for idx, raw_block in enumerate(raw_blocks):
        block_id = int(raw_block.get("number", idx))
        block_type = int(raw_block.get("type", 0))
        bbox = tuple(float(coord) for coord in raw_block.get("bbox", (0.0, 0.0, 0.0, 0.0)))

        spans: List[TextSpan] = []
        lines_text: List[str] = []

        if block_type == 0:  # Text block
            for line in raw_block.get("lines", []):
                line_spans_text: List[str] = []
                for span_data in line.get("spans", []):
                    span_text = span_data.get("text", "")
                    span_bbox = tuple(
                        float(coord) for coord in span_data.get("bbox", (0.0, 0.0, 0.0, 0.0))
                    )
                    span_font = str(span_data.get("font", ""))
                    span_size = float(span_data.get("size", 0.0))
                    span_flags = int(span_data.get("flags", 0))
                    raw_color = span_data.get("color")
                    span_color = int(raw_color) if raw_color is not None else None

                    spans.append(
                        TextSpan(
                            text=span_text,
                            bbox=span_bbox,
                            font=span_font,
                            font_size=span_size,
                            flags=span_flags,
                            color=span_color,
                        )
                    )
                    line_spans_text.append(span_text)
                lines_text.append("".join(line_spans_text))
            block_text = "\n".join(lines_text)
        else:
            # Non-text blocks (e.g., raster images or vector graphics)
            block_text = ""

        blocks.append(
            TextBlock(
                block_id=block_id,
                bbox=bbox,
                text=block_text,
                block_type=block_type,
                spans=spans,
            )
        )

    return blocks


def extract_page(pymupdf_page: pymupdf.Page, page_number: int) -> Page:
    """Extracts a structured Page instance from a PyMuPDF Page object.

    Args:
        pymupdf_page: Active PyMuPDF Page instance.
        page_number: 1-based page index.

    Returns:
        Structured Page instance with geometry and layout blocks.
    """
    width = float(pymupdf_page.rect.width)
    height = float(pymupdf_page.rect.height)
    page_dict = pymupdf_page.get_text("dict")
    blocks = extract_blocks(page_dict)

    return Page(
        page_number=page_number,
        width=width,
        height=height,
        blocks=blocks,
    )


def load_pdf(path: Union[str, Path]) -> Document:
    """Loads and parses a PDF document into a structured Document hierarchy.

    Args:
        path: Path to the target PDF file.

    Returns:
        Structured Document object containing all pages, blocks, and metadata.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is not a valid or readable PDF, or is encrypted.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file does not exist: {path}")

    if not path_obj.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    try:
        doc = pymupdf.open(str(path_obj))
    except Exception as exc:
        raise ValueError(f"Failed to open PDF file '{path}': {exc}") from exc

    try:
        if doc.is_encrypted:
            raise ValueError(f"Encrypted/password-protected PDF is not supported: {path}")

        page_count = len(doc)
        metadata = dict(doc.metadata) if doc.metadata else {}

        pages: List[Page] = []
        for idx in range(page_count):
            pymupdf_page = doc[idx]
            extracted_page = extract_page(pymupdf_page, page_number=idx + 1)
            pages.append(extracted_page)

        return Document(
            source_path=str(path_obj.resolve()),
            page_count=page_count,
            pages=pages,
            metadata=metadata,
        )
    finally:
        doc.close()

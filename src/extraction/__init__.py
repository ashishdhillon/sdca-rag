"""PDF extraction foundation package using PyMuPDF.

Provides structured extraction preserving page numbers, blocks, spans, and typography.
"""

from src.extraction.models import Document, Page, TextBlock, TextSpan
from src.extraction.pdf_parser import extract_blocks, extract_page, load_pdf

__all__ = [
    "Document",
    "Page",
    "TextBlock",
    "TextSpan",
    "load_pdf",
    "extract_page",
    "extract_blocks",
]

"""Data models for structured PDF extraction.

These models represent the structural hierarchy of a PDF document:
    Document -> Page -> TextBlock -> TextSpan

Page numbering follows the 1-based convention standard in academic
and research literature (Page 1 corresponds to the first physical page).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TextSpan:
    """Represents a continuous segment of text sharing identical font styling.

    Attributes:
        text: The string content of the span.
        bbox: Bounding box coordinates (x0, y0, x1, y1) in points.
        font: Font family or name identifier.
        font_size: Font size in typographical points.
        flags: Styling bit flags (e.g., bold, italic).
        color: Optional integer representation of color (sRGB).
    """

    text: str
    bbox: Tuple[float, float, float, float]
    font: str
    font_size: float
    flags: int = 0
    color: Optional[int] = None


@dataclass
class TextBlock:
    """Represents a layout block of text within a document page.

    Attributes:
        block_id: Ordinal identifier of the block on the page in reading order.
        bbox: Bounding box coordinates (x0, y0, x1, y1) in points.
        text: Reconstructed text of the entire block.
        block_type: Block type indicator (0 for text, 1 for image/drawing).
        spans: Ordered list of styling spans contained within this block.
    """

    block_id: int
    bbox: Tuple[float, float, float, float]
    text: str
    block_type: int = 0
    spans: List[TextSpan] = field(default_factory=list)


@dataclass
class Page:
    """Represents an individual page within a PDF document.

    Attributes:
        page_number: 1-based page index (Page 1 is the first page).
        width: Page width in typographical points.
        height: Page height in typographical points.
        blocks: List of structural layout blocks extracted from this page.
    """

    page_number: int
    width: float
    height: float
    blocks: List[TextBlock] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Returns concatenated text from all text blocks on the page."""
        return "\n\n".join(b.text for b in self.blocks if b.text.strip())

    @property
    def text_blocks(self) -> List[TextBlock]:
        """Returns only text-type blocks (block_type == 0)."""
        return [b for b in self.blocks if b.block_type == 0]


@dataclass
class Document:
    """Represents an extracted PDF document.

    Attributes:
        source_path: File system path of the source PDF.
        page_count: Total number of pages in the document.
        pages: List of extracted Page instances in sequential order.
        metadata: Document-level metadata dictionary (title, author, dates, etc.).
    """

    source_path: str
    page_count: int
    pages: List[Page] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Returns concatenated text across all pages in the document."""
        return "\n\n".join(p.text for p in self.pages if p.text.strip())

"""Structure detection module for SDCA.

Extracts logical document hierarchy (Sections, Headings, Paragraphs) using
deterministic typography, layout geometry, and textual patterns from Phase 1.
Operates without embeddings, semantic similarity, LLMs, or neural models.
"""

from collections import Counter
from dataclasses import dataclass, field
import re
from typing import Any, List, Optional, Tuple

from src.baselines.tokenization import get_token_counter
from src.extraction.models import Document, Page, TextBlock


# Canonical academic section titles commonly found in research papers
CANONICAL_SECTION_TITLES = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "prior work",
    "preliminaries",
    "problem formulation",
    "system model",
    "methodology",
    "methods",
    "proposed method",
    "proposed algorithm",
    "system architecture",
    "implementation",
    "implementation details",
    "experimental setup",
    "experiments",
    "results",
    "experimental results",
    "evaluation",
    "discussion",
    "limitations",
    "conclusion",
    "conclusions",
    "future work",
    "references",
    "appendix",
    "acknowledgments",
}

# Regex pattern for numbered academic headings (e.g., '1. Introduction', '2.1 System Model', 'IV. EVALUATION')
NUMBERED_HEADING_PATTERN = re.compile(
    r"^(?:(?:Section|Chapter)\s+\d+[:.]?|(?:\d+\.)+\d*|[IVXLCDM]+\.)\s+[A-Za-z]",
    re.IGNORECASE,
)


@dataclass
class Paragraph:
    """Represents a structural body paragraph within a document section.

    Attributes:
        text: Normalized text content of the paragraph.
        page_number: 1-based page index where the paragraph resides.
        block_id: Ordinal identifier of the source TextBlock.
        token_count: Precalculated token count for the paragraph text.
    """

    text: str
    page_number: int
    block_id: int
    token_count: int


@dataclass
class Section:
    """Represents a coherent document section comprised of an optional heading and paragraphs.

    Attributes:
        section_id: Ordinal index of the section in document reading order.
        heading: Title text of the heading if detected, otherwise None (e.g., for preamble).
        heading_block_id: Source block ID of the heading block.
        paragraphs: Sequential list of Paragraph instances belonging to this section.
        page_start: 1-based page number where the section begins.
        page_end: 1-based page number where the section ends.
    """

    section_id: int
    heading: Optional[str]
    heading_block_id: Optional[int]
    paragraphs: List[Paragraph] = field(default_factory=list)
    page_start: int = 1
    page_end: int = 1

    @property
    def total_tokens(self) -> int:
        """Returns aggregate token count of heading and all contained paragraphs."""
        return sum(p.token_count for p in self.paragraphs)


class HeadingDetector:
    """Deterministic, rule-based heading detector based on typography and layout cues."""

    @staticmethod
    def compute_body_font_size(document: Document) -> float:
        """Computes the dominant (modal) body font size in points across the document.

        Weights font sizes by character length to identify the standard running text size.
        """
        size_counter: Counter = Counter()

        for page in document.pages:
            for block in page.blocks:
                if block.block_type != 0:
                    continue
                for span in block.spans:
                    text_len = len(span.text.strip())
                    if text_len > 0:
                        size_counter[round(span.font_size, 1)] += text_len

        if not size_counter:
            return 10.0  # Standard fallback point size

        # Dominant font size is the one with the highest total character count
        dominant_size, _ = size_counter.most_common(1)[0]
        return float(dominant_size)

    @classmethod
    def is_heading(
        cls,
        block: TextBlock,
        body_font_size: float,
        page: Page,
    ) -> Tuple[bool, Optional[str]]:
        """Determines if a TextBlock constitutes a section heading.

        Args:
            block: Candidate TextBlock.
            body_font_size: Dominant body text font size for the document.
            page: Containing Page instance (for margin/dimension context).

        Returns:
            Tuple of (is_heading: bool, heading_title: Optional[str]).
        """
        if block.block_type != 0:
            return False, None

        raw_text = block.text.strip()
        if not raw_text:
            return False, None

        # Headings are concise: typically <= 25 words and <= 160 characters
        words = raw_text.split()
        if len(words) > 25 or len(raw_text) > 160:
            return False, None

        # Exclude running headers/footers based on vertical margin placement
        x0, y0, x1, y1 = block.bbox
        # Near extreme top (< 5% of page height) or extreme bottom (> 95% of page height)
        if y1 < (page.height * 0.05) or y0 > (page.height * 0.95):
            # If it's a lone number (page number) or very short, reject as header/footer
            if raw_text.isdigit() or len(words) <= 3:
                return False, None

        # Extract maximum font size and bold styling within the block
        max_span_size = max((s.font_size for s in block.spans), default=body_font_size)
        is_bold = any(
            bool(s.flags & 4 or s.flags & 16 or "bold" in s.font.lower() or "black" in s.font.lower())
            for s in block.spans
        )

        clean_title = " ".join(words)

        # Exclude repository stamps (e.g., arXiv watermarks), emails, and copyright notices
        if re.search(r"\barxiv:\d+\.\d+", clean_title, re.IGNORECASE) or clean_title.lower().startswith("arxiv:"):
            return False, None
        if "@" in clean_title:
            return False, None
        if re.match(r"^(?:copyright|all rights reserved|permission to make|provided proper attribution)\b", clean_title, re.IGNORECASE):
            return False, None

        # Rule 1: Numbered heading pattern (e.g., '1. Introduction', '3.2 Proposed Method')
        if NUMBERED_HEADING_PATTERN.match(clean_title):
            # Numbered headings are strong structural signals even if font size is close to body
            return True, clean_title

        # Rule 2: Canonical academic section name
        normalized_lower = clean_title.lower().rstrip(":")
        if normalized_lower in CANONICAL_SECTION_TITLES:
            return True, clean_title

        # If text ends with full-stop period and is not numbered, it is likely a short body sentence
        if clean_title.endswith((".", "?", "!")):
            return False, None

        # Rule 3: Significant font size prominence (>= 15% larger than body font)
        if max_span_size >= (body_font_size * 1.15):
            return True, clean_title

        # Rule 4: Styled prominence (bold and >= body font size)
        if is_bold and max_span_size >= (body_font_size * 1.05):
            return True, clean_title

        return False, None


def detect_document_structure(
    document: Document,
    tokenizer: Optional[Any] = None,
) -> List[Section]:
    """Parses an extracted Document into an ordered hierarchy of Section instances.

    Args:
        document: Phase 1 extracted Document.
        tokenizer: Optional token counter callable or Tokenizer instance.

    Returns:
        Ordered list of Section instances containing headings and paragraphs.
    """
    token_counter = get_token_counter(tokenizer)
    body_font_size = HeadingDetector.compute_body_font_size(document)

    sections: List[Section] = []
    current_section: Optional[Section] = None

    for page in document.pages:
        for block in page.blocks:
            if block.block_type != 0:
                continue

            block_text = block.text.strip()
            if not block_text:
                continue

            is_hd, heading_title = HeadingDetector.is_heading(block, body_font_size, page)

            if is_hd:
                # Close previous section if it exists
                if current_section is not None:
                    sections.append(current_section)

                # Start new section with detected heading
                current_section = Section(
                    section_id=len(sections),
                    heading=heading_title,
                    heading_block_id=block.block_id,
                    paragraphs=[],
                    page_start=page.page_number,
                    page_end=page.page_number,
                )
            else:
                # Body text paragraph
                tokens = token_counter(block_text)
                para = Paragraph(
                    text=block_text,
                    page_number=page.page_number,
                    block_id=block.block_id,
                    token_count=tokens,
                )

                if current_section is None:
                    # Document preamble before first explicit section heading
                    current_section = Section(
                        section_id=0,
                        heading=None,
                        heading_block_id=None,
                        paragraphs=[],
                        page_start=page.page_number,
                        page_end=page.page_number,
                    )

                current_section.paragraphs.append(para)
                current_section.page_end = page.page_number

    if current_section is not None:
        sections.append(current_section)

    return sections

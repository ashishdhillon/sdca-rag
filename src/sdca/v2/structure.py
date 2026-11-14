"""Structure detection module for SDCA V2.

Enhancements in V2:
1. Hierarchical Heading Levels: Deterministically infers heading levels (Level 1, 2, 3)
   from numbered patterns, canonical academic taxonomy, and typographical prominence.
2. Section Hierarchy Tree & Path: Tracks parent headings and full ancestral paths
   (e.g., '3. Model Architecture > 3.2 Attention > 3.2.1 Scaled Dot-Product Attention').
3. Heading-Content Binding: Avoids creating orphaned, empty sections for umbrella
   headings; maintains them in the hierarchy stack so subsequent subsections inherit
   full context.
"""

from collections import Counter
from dataclasses import dataclass, field
import re
from typing import Any, List, Optional, Tuple

from src.baselines.tokenization import get_token_counter
from src.extraction.models import Document, Page, TextBlock
from src.sdca.structure import (
    CANONICAL_SECTION_TITLES,
    NUMBERED_HEADING_PATTERN,
    Paragraph,
)


@dataclass
class HeadingNode:
    """Represents an active heading node within the document hierarchy."""

    title: str
    level: int  # 1 for major section, 2 for subsection, 3 for sub-subsection
    block_id: int
    page_number: int


@dataclass
class SectionV2:
    """Represents a structured document section with hierarchical ancestry in SDCA V2.

    Attributes:
        section_id: Ordinal index of the section.
        heading: Title of the immediate heading (or None for preamble).
        parent_heading: Title of the direct parent heading in hierarchy, if any.
        section_path: List of titles representing the full path from root to this section.
        level: Hierarchical depth level (1, 2, 3...).
        heading_block_id: Source block ID of the immediate heading block.
        paragraphs: Sequential list of Paragraph instances.
        page_start: Starting 1-based page number.
        page_end: Ending 1-based page number.
    """

    section_id: int
    heading: Optional[str]
    parent_heading: Optional[str]
    section_path: List[str] = field(default_factory=list)
    level: int = 1
    heading_block_id: Optional[int] = None
    paragraphs: List[Paragraph] = field(default_factory=list)
    page_start: int = 1
    page_end: int = 1

    @property
    def section_path_str(self) -> str:
        """Returns the breadcrumb string representation of the section hierarchy."""
        if not self.section_path:
            return self.heading or "General"
        return " > ".join(self.section_path)

    @property
    def total_tokens(self) -> int:
        """Aggregate token count of all paragraphs in this section."""
        return sum(p.token_count for p in self.paragraphs)


class HeadingDetectorV2:
    """Deterministic rule-based heading detector with hierarchy depth inference."""

    @staticmethod
    def compute_body_font_size(document: Document) -> float:
        """Computes the dominant (modal) body font size in points across the document."""
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
            return 10.0

        dominant_size, _ = size_counter.most_common(1)[0]
        return float(dominant_size)

    @classmethod
    def infer_heading_level(
        cls,
        title: str,
        max_span_size: float,
        body_font_size: float,
    ) -> int:
        """Deterministically calculates hierarchical depth level for a heading.

        Returns:
            1: Major top-level section (e.g., '1. Introduction', 'Abstract')
            2: Subsection (e.g., '3.2 Attention')
            3: Sub-subsection (e.g., '3.2.1 Scaled Dot-Product Attention')
        """
        clean = title.strip()

        # Check numbered pattern depth
        # Match numbered prefixes like '1.', '1.2', '1.2.3' or 'Article 4', 'Section 9.2', 'ITEM 7'
        num_match = re.match(
            r"^(?:(?:Section|Chapter|Article|Item|Note|Schedule|Exhibit)\s+)?((?:\d+\.)+\d*|\d+|[IVXLCDM]+)\b",
            clean,
            re.IGNORECASE,
        )
        if num_match:
            prefix = num_match.group(1).rstrip(".")
            parts = prefix.split(".")
            if len(parts) > 1:
                return min(len(parts), 3)
            return 1

        # Roman numerals or 'Section X' -> Level 1
        if re.match(r"^(?:[IVXLCDM]+\.|(?:Section|Chapter|Article|Item|Note|Schedule|Exhibit)\s+\d+[:.]?)\s+", clean, re.IGNORECASE):
            return 1

        # Canonical section titles are always Level 1
        normalized_lower = clean.lower().rstrip(":")
        if normalized_lower in CANONICAL_SECTION_TITLES:
            return 1

        # Typography-based level inference
        if max_span_size >= (body_font_size * 1.30):
            return 1
        elif max_span_size >= (body_font_size * 1.15):
            return 2
        else:
            return 3

    @classmethod
    def is_heading(
        cls,
        block: TextBlock,
        body_font_size: float,
        page: Page,
    ) -> Tuple[bool, Optional[str], int]:
        """Determines if a block is a heading and computes its hierarchical level.

        Returns:
            Tuple of (is_heading: bool, heading_title: Optional[str], level: int)
        """
        if block.block_type != 0:
            return False, None, 1

        raw_text = block.text.strip()
        if not raw_text:
            return False, None, 1

        words = raw_text.split()
        if len(words) > 25 or len(raw_text) > 160:
            return False, None, 1

        # Margin exclusions for header/footer
        x0, y0, x1, y1 = block.bbox
        if y1 < (page.height * 0.05) or y0 > (page.height * 0.95):
            if raw_text.isdigit() or len(words) <= 3:
                return False, None, 1

        max_span_size = max((s.font_size for s in block.spans), default=body_font_size)
        is_bold = any(
            bool(s.flags & 4 or s.flags & 16 or "bold" in s.font.lower() or "black" in s.font.lower())
            for s in block.spans
        )

        clean_title = " ".join(words)

        # Filter repository stamps, emails, copyright notices
        if re.search(r"\barxiv:\d+\.\d+", clean_title, re.IGNORECASE) or clean_title.lower().startswith("arxiv:"):
            return False, None, 1
        if "@" in clean_title:
            return False, None, 1
        if re.match(r"^(?:copyright|all rights reserved|permission to make|provided proper attribution)\b", clean_title, re.IGNORECASE):
            return False, None, 1

        # Criteria check
        is_hd = False
        if NUMBERED_HEADING_PATTERN.match(clean_title):
            is_hd = True
        elif clean_title.lower().rstrip(":") in CANONICAL_SECTION_TITLES:
            is_hd = True
        elif not clean_title.endswith((".", "?", "!")):
            if max_span_size >= (body_font_size * 1.15):
                is_hd = True
            elif is_bold and max_span_size >= (body_font_size * 1.05):
                is_hd = True

        if is_hd:
            level = cls.infer_heading_level(clean_title, max_span_size, body_font_size)
            return True, clean_title, level

        return False, None, 1


def detect_document_structure_v2(
    document: Document,
    tokenizer: Optional[Any] = None,
) -> List[SectionV2]:
    """Parses a Document into an ordered hierarchy of SectionV2 instances with breadcrumbs.

    Heading-Content Binding:
    If an umbrella heading occurs without immediate body text (e.g. '3. Model Architecture'
    directly preceding '3.1 Encoder Stack'), it is maintained on the hierarchy stack
    rather than being discarded or emitted as an isolated empty section.
    """
    token_counter = get_token_counter(tokenizer)
    body_font_size = HeadingDetectorV2.compute_body_font_size(document)

    sections: List[SectionV2] = []
    hierarchy_stack: List[HeadingNode] = []
    current_section: Optional[SectionV2] = None

    for page in document.pages:
        for block in page.blocks:
            if block.block_type != 0:
                continue

            block_text = block.text.strip()
            if not block_text:
                continue

            is_hd, heading_title, level = HeadingDetectorV2.is_heading(block, body_font_size, page)

            if is_hd and heading_title:
                # Update hierarchy stack: pop any ancestors at or below the new heading's level
                while hierarchy_stack and hierarchy_stack[-1].level >= level:
                    hierarchy_stack.pop()

                node = HeadingNode(
                    title=heading_title,
                    level=level,
                    block_id=block.block_id,
                    page_number=page.page_number,
                )
                hierarchy_stack.append(node)

                # Determine ancestral breadcrumb path
                sec_path = [h.title for h in hierarchy_stack]
                parent = hierarchy_stack[-2].title if len(hierarchy_stack) > 1 else None

                # If current_section has paragraphs, finalize it
                if current_section is not None and current_section.paragraphs:
                    sections.append(current_section)
                    current_section = None

                # Initiate new SectionV2
                current_section = SectionV2(
                    section_id=len(sections),
                    heading=heading_title,
                    parent_heading=parent,
                    section_path=sec_path,
                    level=level,
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
                    # Document preamble before first heading
                    current_section = SectionV2(
                        section_id=0,
                        heading=None,
                        parent_heading=None,
                        section_path=["Preamble"],
                        level=1,
                        heading_block_id=None,
                        paragraphs=[],
                        page_start=page.page_number,
                        page_end=page.page_number,
                    )

                current_section.paragraphs.append(para)
                current_section.page_end = page.page_number

    if current_section is not None and current_section.paragraphs:
        sections.append(current_section)

    return sections

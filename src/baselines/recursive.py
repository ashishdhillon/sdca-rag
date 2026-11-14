"""Recursive chunking baseline algorithm.

Implements a hierarchical text-splitting strategy that attempts to preserve
higher-level boundaries (paragraphs, then lines, then sentences, then words)
before falling back to smaller units.
Does not use layout geometry, font hierarchy, or heading detection.
"""

import re
from typing import Any, Callable, List, Optional, Tuple, Union

from src.baselines.models import Chunk
from src.baselines.tokenization import (
    build_document_text_and_spans,
    get_token_counter,
    resolve_page_range,
)
from src.extraction.models import Document


def _split_into_units(
    text: str,
    start_offset: int,
    separator_level: int,
    target_tokens: int,
    token_counter: Callable[[str], int],
) -> List[Tuple[str, int, int]]:
    """Recursively decomposes text into atomic units that fit within target_tokens.

    Levels:
        0: Paragraph boundaries (\n\n)
        1: Line boundaries (\n)
        2: Sentence boundaries (punctuation + space)
        3: Word boundaries (space)
        4: Character fallback (emergency splitting for oversized words)
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    tokens = token_counter(clean_text)
    if tokens <= target_tokens:
        # Fits completely within target tokens
        return [(clean_text, start_offset, start_offset + len(text))]

    # Level 0: Paragraphs
    if separator_level == 0:
        parts = text.split("\n\n")
        if len(parts) > 1:
            units: List[Tuple[str, int, int]] = []
            curr_pos = start_offset
            for p in parts:
                p_len = len(p)
                p_clean = p.strip()
                if p_clean:
                    units.extend(
                        _split_into_units(
                            p,
                            curr_pos,
                            separator_level=1,
                            target_tokens=target_tokens,
                            token_counter=token_counter,
                        )
                    )
                curr_pos += p_len + 2  # account for len('\n\n')
            return units
        separator_level = 1

    # Level 1: Lines
    if separator_level == 1:
        parts = text.split("\n")
        if len(parts) > 1:
            units = []
            curr_pos = start_offset
            for p in parts:
                p_len = len(p)
                p_clean = p.strip()
                if p_clean:
                    units.extend(
                        _split_into_units(
                            p,
                            curr_pos,
                            separator_level=2,
                            target_tokens=target_tokens,
                            token_counter=token_counter,
                        )
                    )
                curr_pos += p_len + 1  # account for len('\n')
            return units
        separator_level = 2

    # Level 2: Sentence boundaries (.!? followed by whitespace)
    if separator_level == 2:
        # Match sentence end punctuation followed by whitespace
        matches = list(re.finditer(r"([.!?]+)(\s+)", text))
        if matches:
            units = []
            last_end = 0
            for m in matches:
                sent_text = text[last_end : m.end(1)].strip()
                sent_offset = start_offset + last_end
                if sent_text:
                    units.extend(
                        _split_into_units(
                            sent_text,
                            sent_offset,
                            separator_level=3,
                            target_tokens=target_tokens,
                            token_counter=token_counter,
                        )
                    )
                last_end = m.end()

            remainder = text[last_end:].strip()
            if remainder:
                units.extend(
                    _split_into_units(
                        remainder,
                        start_offset + last_end,
                        separator_level=3,
                        target_tokens=target_tokens,
                        token_counter=token_counter,
                    )
                )
            return units
        separator_level = 3

    # Level 3: Words (space-delimited)
    if separator_level == 3:
        words = list(re.finditer(r"\S+", text))
        if len(words) > 1:
            units = []
            for w in words:
                w_text = w.group()
                w_offset = start_offset + w.start()
                units.extend(
                    _split_into_units(
                        w_text,
                        w_offset,
                        separator_level=4,
                        target_tokens=target_tokens,
                        token_counter=token_counter,
                    )
                )
            return units
        separator_level = 4

    # Level 4: Character fallback (extreme oversized unit without whitespace)
    mid = len(text) // 2
    if mid > 0:
        left = _split_into_units(
            text[:mid],
            start_offset,
            separator_level=4,
            target_tokens=target_tokens,
            token_counter=token_counter,
        )
        right = _split_into_units(
            text[mid:],
            start_offset + mid,
            separator_level=4,
            target_tokens=target_tokens,
            token_counter=token_counter,
        )
        return left + right

    return [(clean_text, start_offset, start_offset + len(text))]


def chunk_recursive(
    document: Union[Document, str],
    target_tokens: int = 400,
    tokenizer: Optional[Any] = None,
) -> List[Chunk]:
    """Partitions a document hierarchically into chunks honoring textual boundaries.

    Attempts to preserve paragraphs, then lines, then sentences, and lastly words.

    Args:
        document: Extracted Document instance or raw text string.
        target_tokens: Upper token threshold for each chunk. Defaults to 400.
        tokenizer: Optional custom tokenizer or token count callable.

    Returns:
        List of Chunk instances maintaining sequential document order.

    Raises:
        ValueError: If target_tokens <= 0.
    """
    if target_tokens <= 0:
        raise ValueError(f"target_tokens must be positive, got {target_tokens}")

    full_text, page_spans = build_document_text_and_spans(document)
    if not full_text.strip():
        return []

    token_counter = get_token_counter(tokenizer)

    # 1. Break down into atomic units that each satisfy <= target_tokens
    units = _split_into_units(
        full_text,
        start_offset=0,
        separator_level=0,
        target_tokens=target_tokens,
        token_counter=token_counter,
    )

    if not units:
        return []

    # 2. Merge adjacent units sequentially without exceeding target_tokens
    chunks: List[Chunk] = []
    current_units: List[Tuple[str, int, int]] = []

    for unit in units:
        if not current_units:
            current_units.append(unit)
            continue

        cand_start = current_units[0][1]
        cand_end = unit[2]
        candidate_text = full_text[cand_start:cand_end].strip()
        cand_tokens = token_counter(candidate_text)

        if cand_tokens <= target_tokens:
            current_units.append(unit)
        else:
            # Emit current accumulated group
            c_start = current_units[0][1]
            c_end = current_units[-1][2]
            c_text = full_text[c_start:c_end].strip()
            if c_text:
                page_start, page_end = resolve_page_range(c_start, c_end, page_spans)
                chunks.append(
                    Chunk(
                        chunk_id=f"recursive_{len(chunks)}",
                        text=c_text,
                        page_start=page_start,
                        page_end=page_end,
                        token_count=token_counter(c_text),
                        strategy="recursive",
                        section=None,
                        metadata={"target_tokens": target_tokens},
                    )
                )
            current_units = [unit]

    if current_units:
        c_start = current_units[0][1]
        c_end = current_units[-1][2]
        c_text = full_text[c_start:c_end].strip()
        if c_text:
            page_start, page_end = resolve_page_range(c_start, c_end, page_spans)
            chunks.append(
                Chunk(
                    chunk_id=f"recursive_{len(chunks)}",
                    text=c_text,
                    page_start=page_start,
                    page_end=page_end,
                    token_count=token_counter(c_text),
                    strategy="recursive",
                    section=None,
                    metadata={"target_tokens": target_tokens},
                )
            )

    return chunks

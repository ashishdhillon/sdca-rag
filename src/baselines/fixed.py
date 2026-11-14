"""Fixed-size chunking baseline algorithm.

Implements a standard sequential sliding-window chunker with configurable
target token count and overlap. This baseline does not inspect font hierarchy,
layout geometry, or document structure.
"""

from typing import Any, List, Optional, Union

from src.baselines.models import Chunk
from src.baselines.tokenization import (
    RegexTokenizer,
    build_document_text_and_spans,
    get_token_counter,
    resolve_page_range,
)
from src.extraction.models import Document


def chunk_fixed(
    document: Union[Document, str],
    target_tokens: int = 400,
    overlap_tokens: Optional[int] = None,
    tokenizer: Optional[Any] = None,
) -> List[Chunk]:
    """Partitions a document using a fixed-size sliding token window.

    Args:
        document: Extracted Document instance or raw text string.
        target_tokens: Desired token capacity per chunk. Defaults to 400.
        overlap_tokens: Number of overlapping tokens between successive chunks.
            Defaults to 50 (or max(0, target_tokens // 4) if target_tokens <= 50).
        tokenizer: Optional custom tokenizer or token count callable.

    Returns:
        List of Chunk instances strictly ordered as they appear in the source text.

    Raises:
        ValueError: If target_tokens <= 0, overlap_tokens < 0, or overlap_tokens >= target_tokens.
    """
    if target_tokens <= 0:
        raise ValueError(f"target_tokens must be positive, got {target_tokens}")

    if overlap_tokens is None:
        overlap = 50 if target_tokens > 50 else max(0, target_tokens // 4)
    else:
        overlap = overlap_tokens

    if overlap < 0:
        raise ValueError(f"overlap_tokens cannot be negative, got {overlap}")
    if overlap >= target_tokens:
        raise ValueError(
            f"overlap_tokens ({overlap}) must be strictly less than "
            f"target_tokens ({target_tokens})"
        )

    full_text, page_spans = build_document_text_and_spans(document)
    if not full_text.strip():
        return []

    token_counter = get_token_counter(tokenizer)

    # Use tokenizer spans for exact character mapping without destroying formatting
    if hasattr(tokenizer, "find_token_spans") and callable(tokenizer.find_token_spans):
        token_spans = tokenizer.find_token_spans(full_text)
    else:
        tok = RegexTokenizer()
        token_spans = tok.find_token_spans(full_text)

    if not token_spans:
        return []

    step = target_tokens - overlap
    chunks: List[Chunk] = []

    for i in range(0, len(token_spans), step):
        window = token_spans[i : i + target_tokens]
        if not window:
            continue

        start_char = window[0].start
        end_char = window[-1].end
        chunk_text = full_text[start_char:end_char].strip()

        if not chunk_text:
            continue

        page_start, page_end = resolve_page_range(start_char, end_char, page_spans)
        actual_tokens = token_counter(chunk_text)
        chunk_id = f"fixed_{len(chunks)}"

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                text=chunk_text,
                page_start=page_start,
                page_end=page_end,
                token_count=actual_tokens,
                strategy="fixed",
                section=None,
                metadata={
                    "target_tokens": target_tokens,
                    "overlap_tokens": overlap,
                },
            )
        )

    return chunks

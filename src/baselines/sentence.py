"""Sentence-based chunking baseline algorithm.

Partitions text by segmenting sentences and grouping complete sentences
toward a target token count without splitting sentences.
Does not use embeddings, LLMs, or neural semantic chunkers.
"""

import re
from typing import Any, List, Optional, Tuple, Union

from src.baselines.models import Chunk
from src.baselines.tokenization import (
    build_document_text_and_spans,
    get_token_counter,
    resolve_page_range,
)
from src.extraction.models import Document


# Common abbreviations protected from erroneous sentence splitting
PROTECTED_ABBREVIATIONS = {
    "dr.",
    "mr.",
    "mrs.",
    "ms.",
    "prof.",
    "sr.",
    "jr.",
    "vs.",
    "etc.",
    "e.g.",
    "i.e.",
    "al.",
    "fig.",
    "eq.",
    "ref.",
}


def segment_sentences(text: str) -> List[Tuple[str, int, int]]:
    """Segments text into complete sentences with character offsets.

    Uses a deterministic rule-based segmentation method handling common abbreviations
    and decimal numbers.

    Args:
        text: Input string.

    Returns:
        List of (sentence_text, start_char_index, end_char_index).
    """
    if not text.strip():
        return []

    # Pattern matches terminal punctuation [.!?] followed by whitespace or string end
    pattern = re.compile(r"([.!?]+)(?:\s+|\Z)")
    sentences: List[Tuple[str, int, int]] = []
    start_idx = 0

    for match in pattern.finditer(text):
        end_punct_idx = match.end(1)

        # Check for abbreviation before the period
        preceding_text = text[start_idx:end_punct_idx]
        word_match = re.search(r"\b\w+\.\Z", preceding_text, re.IGNORECASE)
        if word_match and word_match.group(0).lower() in PROTECTED_ABBREVIATIONS:
            continue

        # Check for numeric decimal pattern (e.g., 3.14)
        if re.search(r"\b\d+\.\Z", preceding_text):
            continue

        sentence_str = text[start_idx:end_punct_idx].strip()
        if sentence_str:
            sentences.append((sentence_str, start_idx, end_punct_idx))
        start_idx = match.end()

    # Capture trailing text after final sentence delimiter
    remainder = text[start_idx:].strip()
    if remainder:
        sentences.append((remainder, start_idx, len(text)))

    return sentences


def chunk_sentence(
    document: Union[Document, str],
    target_tokens: int = 400,
    tokenizer: Optional[Any] = None,
) -> List[Chunk]:
    """Partitions a document by grouping complete sentences up to target_tokens.

    Sentence integrity is strictly preserved; individual sentences are never
    intentionally cleaved.

    Args:
        document: Extracted Document instance or raw text string.
        target_tokens: Target token capacity per chunk. Defaults to 400.
        tokenizer: Optional custom tokenizer or token count callable.

    Returns:
        List of Chunk instances maintaining sentence integrity and original order.

    Raises:
        ValueError: If target_tokens <= 0.
    """
    if target_tokens <= 0:
        raise ValueError(f"target_tokens must be positive, got {target_tokens}")

    full_text, page_spans = build_document_text_and_spans(document)
    if not full_text.strip():
        return []

    token_counter = get_token_counter(tokenizer)
    sentences = segment_sentences(full_text)
    if not sentences:
        return []

    chunks: List[Chunk] = []
    current_sentences: List[Tuple[str, int, int]] = []

    for sent in sentences:
        if not current_sentences:
            current_sentences.append(sent)
            continue

        cand_start = current_sentences[0][1]
        cand_end = sent[2]
        candidate_text = full_text[cand_start:cand_end].strip()
        cand_tokens = token_counter(candidate_text)

        if cand_tokens <= target_tokens:
            current_sentences.append(sent)
        else:
            # Emit accumulated chunk
            c_start = current_sentences[0][1]
            c_end = current_sentences[-1][2]
            c_text = full_text[c_start:c_end].strip()
            if c_text:
                page_start, page_end = resolve_page_range(c_start, c_end, page_spans)
                chunks.append(
                    Chunk(
                        chunk_id=f"sentence_{len(chunks)}",
                        text=c_text,
                        page_start=page_start,
                        page_end=page_end,
                        token_count=token_counter(c_text),
                        strategy="sentence",
                        section=None,
                        metadata={"target_tokens": target_tokens},
                    )
                )
            current_sentences = [sent]

    if current_sentences:
        c_start = current_sentences[0][1]
        c_end = current_sentences[-1][2]
        c_text = full_text[c_start:c_end].strip()
        if c_text:
            page_start, page_end = resolve_page_range(c_start, c_end, page_spans)
            chunks.append(
                Chunk(
                    chunk_id=f"sentence_{len(chunks)}",
                    text=c_text,
                    page_start=page_start,
                    page_end=page_end,
                    token_count=token_counter(c_text),
                    strategy="sentence",
                    section=None,
                    metadata={"target_tokens": target_tokens},
                )
            )

    return chunks

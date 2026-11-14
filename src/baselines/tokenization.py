"""Deterministic tokenization utilities for research experiments.

Guarantees reproducible token counts without relying on character-based heuristics (len(text)/4).
Supports custom tokenizer callables and pre-trained tokenizers.
"""

from dataclasses import dataclass
import re
from typing import Any, Callable, List, Optional, Tuple, Union

from src.extraction.models import Document


@dataclass(frozen=True)
class TokenSpan:
    """Represents a token and its character offsets within the source text."""

    text: str
    start: int
    end: int


class RegexTokenizer:
    """Deterministic regex-based word and punctuation tokenizer.

    Splits text into words and punctuation marks without neural dependencies,
    closely approximating standard subword token counts while remaining 100% deterministic.
    """

    DEFAULT_PATTERN = r"\w+|[^\w\s]"

    def __init__(self, pattern: str = DEFAULT_PATTERN):
        self.pattern = re.compile(pattern)

    def tokenize(self, text: str) -> List[str]:
        """Returns list of token strings."""
        return self.pattern.findall(text)

    def count_tokens(self, text: str) -> int:
        """Returns exact count of tokens in text."""
        return len(self.tokenize(text))

    def find_token_spans(self, text: str) -> List[TokenSpan]:
        """Finds tokens along with their exact start and end character offsets."""
        return [
            TokenSpan(text=m.group(), start=m.start(), end=m.end())
            for m in self.pattern.finditer(text)
        ]


def get_token_counter(
    tokenizer: Optional[Union[RegexTokenizer, Callable[[str], int], Any]] = None
) -> Callable[[str], int]:
    """Resolves a consistent token counting function from a tokenizer instance or callable.

    Args:
        tokenizer: An instance with `count_tokens` method, or a callable `(str) -> int`,
            or None (defaults to RegexTokenizer).

    Returns:
        Callable taking a string and returning an integer token count.
    """
    if tokenizer is None:
        default_tok = RegexTokenizer()
        return default_tok.count_tokens

    if hasattr(tokenizer, "count_tokens") and callable(tokenizer.count_tokens):
        return tokenizer.count_tokens

    if callable(tokenizer):
        return tokenizer

    raise ValueError(
        f"Unsupported tokenizer type '{type(tokenizer)}'. Must provide a callable "
        "or an object with a `count_tokens(text: str) -> int` method."
    )


def build_document_text_and_spans(
    document: Union[Document, str],
) -> Tuple[str, List[Tuple[int, int, int]]]:
    """Extracts unified document text while indexing character offsets to 1-based page numbers.

    Args:
        document: Phase 1 Document instance or plain text string.

    Returns:
        Tuple of:
            full_text: Assembled text content.
            page_spans: List of (page_number, start_char, end_char) boundaries.
    """
    if isinstance(document, str):
        text = document.strip()
        if not text:
            return "", []
        return text, [(1, 0, len(text))]

    if not isinstance(document, Document):
        raise TypeError(f"Expected Document or str, got {type(document).__name__}")

    full_text_parts: List[str] = []
    page_spans: List[Tuple[int, int, int]] = []
    current_char_idx = 0

    for page in document.pages:
        page_text = page.text.strip()
        if not page_text:
            continue

        if full_text_parts:
            # Two newlines between pages to delineate page boundaries cleanly
            full_text_parts.append("\n\n")
            current_char_idx += 2

        start_char = current_char_idx
        full_text_parts.append(page_text)
        current_char_idx += len(page_text)
        end_char = current_char_idx

        page_spans.append((page.page_number, start_char, end_char))

    full_text = "".join(full_text_parts)
    return full_text, page_spans


def resolve_page_range(
    start_char: int,
    end_char: int,
    page_spans: List[Tuple[int, int, int]],
) -> Tuple[int, int]:
    """Maps start and end character offsets in full text to 1-based (page_start, page_end).

    Args:
        start_char: Beginning character index of the chunk in unified text.
        end_char: Ending character index of the chunk in unified text.
        page_spans: Ordered list of (page_number, start_offset, end_offset).

    Returns:
        Tuple of (page_start, page_end). Defaults to (1, 1) if page spans are empty.
    """
    if not page_spans:
        return 1, 1

    page_start = page_spans[0][0]
    page_end = page_spans[-1][0]

    # Find page where start_char falls
    for p_num, s, e in page_spans:
        if start_char < e:
            page_start = p_num
            break

    # Find page where last character (end_char - 1) falls
    last_char = max(start_char, end_char - 1)
    for p_num, s, e in reversed(page_spans):
        if last_char >= s:
            page_end = p_num
            break

    return page_start, page_end

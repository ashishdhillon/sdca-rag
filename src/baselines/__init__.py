"""Baseline chunking strategies package for RAG evaluation.

Provides standard comparative chunking methods:
- Fixed-size chunking (chunk_fixed)
- Hierarchical recursive chunking (chunk_recursive)
- Sentence-based chunking (chunk_sentence)
"""

from src.baselines.fixed import chunk_fixed
from src.baselines.models import Chunk
from src.baselines.recursive import chunk_recursive
from src.baselines.sentence import chunk_sentence, segment_sentences
from src.baselines.tokenization import (
    RegexTokenizer,
    TokenSpan,
    build_document_text_and_spans,
    get_token_counter,
    resolve_page_range,
)

__all__ = [
    "Chunk",
    "chunk_fixed",
    "chunk_recursive",
    "chunk_sentence",
    "RegexTokenizer",
    "TokenSpan",
    "segment_sentences",
    "get_token_counter",
    "build_document_text_and_spans",
    "resolve_page_range",
]

"""Data models for baseline chunking strategies.

Provides the common Chunk data structure shared across all chunking methods
(both baselines and future SDCA algorithm) to ensure consistent evaluation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Chunk:
    """Represents an extracted and segmented chunk of text from a document.

    Attributes:
        chunk_id: Unique string identifier for the chunk (e.g., 'fixed_0').
        text: Normalized textual content of the chunk.
        page_start: 1-based page index where the chunk content begins.
        page_end: 1-based page index where the chunk content ends.
        token_count: Number of tokens contained in the chunk text.
        strategy: Identifier of the chunking algorithm used ('fixed', 'recursive', 'sentence').
        section: Structural section/heading title if available. Defaults to None in Phase 2
            baselines because structural intelligence is exclusively reserved for SDCA.
        metadata: Dictionary tracking auxiliary experimental configuration parameters
            (e.g., target_tokens, overlap_tokens) for complete research reproducibility.
    """

    chunk_id: str
    text: str
    page_start: int
    page_end: int
    token_count: int
    strategy: str
    section: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_text: Optional[str] = None


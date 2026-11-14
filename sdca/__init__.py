"""SDCA: Structure-Aware Document Chunking Algorithm for Retrieval-Augmented Generation (RAG) Systems.

Developed by Subodh Butt & Ashish Dhillon.
"""

from src.baselines.models import Chunk
from src.extraction.models import Document
from src.extraction.pdf_parser import load_pdf
from src.retrieval.hybrid import BM25, rrf, structure_guided_rrf
from src.sdca.chunker import chunk_sdca
from src.sdca.v2.chunker import chunk_sdca_v2
from src.sdca.v3.chunker import V3Options, chunk_sdca_stair, chunk_sdca_v3

__version__ = "0.1.0"
__all__ = [
    "chunk_document",
    "load_pdf",
    "chunk_sdca_stair",
    "chunk_sdca_v2",
    "chunk_sdca",
    "structure_guided_rrf",
    "SDCATextSplitter",
    "Chunk",
    "Document",
    "V3Options",
]


def chunk_document(pdf_path: str, target_tokens: int = 300, **kwargs):
    """High-level convenience API to load and chunk any PDF using the champion SDCA algorithm.
    
    Args:
        pdf_path: Path to the target PDF document.
        target_tokens: Desired target token size per chunk (default: 300).
        
    Returns:
        List of layout-aware Chunk objects.
    """
    doc = load_pdf(pdf_path)
    return chunk_sdca_stair(doc, target_tokens=target_tokens, **kwargs)


class SDCATextSplitter:
    """Drop-in LangChain-compatible Document Transformer for SDCA."""

    def __init__(self, target_tokens: int = 300, min_tokens: int = 120, max_tokens: int = 420, **kwargs):
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.kwargs = kwargs

    def split_pdf(self, pdf_path: str):
        """Chunks a PDF document preserving section hierarchies and tables."""
        return chunk_document(
            pdf_path,
            target_tokens=self.target_tokens,
            min_tokens=self.min_tokens,
            max_tokens=self.max_tokens,
            **self.kwargs,
        )

"""SDCA (Structure-Aware Document Chunking Algorithm) package.

Proposed research algorithm for layout-aware document chunking.
"""

from src.sdca.chunker import chunk_sdca
from src.sdca.v2.chunker import chunk_sdca_v2
from src.sdca.structure import (
    HeadingDetector,
    Paragraph,
    Section,
    detect_document_structure,
)

__all__ = [
    "chunk_sdca",
    "chunk_sdca_v2",
    "detect_document_structure",
    "HeadingDetector",
    "Section",
    "Paragraph",
]


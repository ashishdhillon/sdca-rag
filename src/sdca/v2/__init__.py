"""SDCA V2 (Structure-Aware Document Chunking Algorithm V2) Package.

Provides enhanced structure-aware chunking with:
- Heading-content binding
- Hierarchical section context
- Structure-aware retrieval representations
- Adaptive small-chunk merging within hierarchy
"""

from src.sdca.v2.chunker import chunk_sdca_v2
from src.sdca.v2.structure import (
    HeadingDetectorV2,
    HeadingNode,
    SectionV2,
    detect_document_structure_v2,
)

__all__ = [
    "chunk_sdca_v2",
    "HeadingDetectorV2",
    "HeadingNode",
    "SectionV2",
    "detect_document_structure_v2",
]

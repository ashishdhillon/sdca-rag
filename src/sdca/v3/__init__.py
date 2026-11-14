"""SDCA V3: V2 plus hierarchy repair, non-body filtering, and a hard size floor.

Every change is individually switchable via ``V3Options`` so that each can be
ablated in the paper. V2 is left untouched; V3 post-processes V2 output.
"""

from src.sdca.v3.chunker import V3Options, chunk_sdca_v3, chunk_sdca_stair

__all__ = ["V3Options", "chunk_sdca_v3", "chunk_sdca_stair"]

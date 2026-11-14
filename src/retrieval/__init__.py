"""Retrieval package for SDCA comparative experiments.

Provides dense vector embedding generation with Sentence Transformers and
exact cosine similarity retrieval with FAISS IndexFlatIP.
"""

from src.retrieval.embeddings import EmbeddingManager, ModelTokenizer
from src.retrieval.faiss_store import FAISSVectorStore

__all__ = ["EmbeddingManager", "ModelTokenizer", "FAISSVectorStore"]

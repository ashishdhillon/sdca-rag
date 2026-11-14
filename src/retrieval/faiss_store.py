"""FAISS Vector Store using exact Cosine Similarity (IndexFlatIP).

Maintains Ceteris Paribus controls:
1. Exact dense vector search without lossy quantization (IndexFlatIP).
2. L2 normalized input vectors ensure Inner Product strictly computes Cosine Similarity.
3. Preserves Chunk metadata and maps index positions directly to Chunk instances.
"""

from typing import List, Optional, Tuple
import numpy as np

from src.baselines.models import Chunk


class FAISSVectorStore:
    """In-memory FAISS vector index using IndexFlatIP for exact cosine similarity search."""

    def __init__(self, dimension: int = 384):
        """Initializes an empty FAISS IndexFlatIP.

        Args:
            dimension: Dimensionality of embedding vectors (default: 384 for all-MiniLM-L6-v2).
        """
        import faiss

        self.dimension = int(dimension)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks: List[Chunk] = []

    @property
    def total_vectors(self) -> int:
        """Returns total number of indexed vectors."""
        return int(self.index.ntotal)

    def __len__(self) -> int:
        return self.total_vectors

    def add_chunks(self, chunks: List[Chunk], embeddings: np.ndarray) -> None:
        """Adds chunks and their corresponding dense vectors to the FAISS index.

        Args:
            chunks: List of Chunk objects to store.
            embeddings: 2D numpy array of shape (len(chunks), dimension).

        Raises:
            ValueError: If chunks count does not match embeddings rows, or vector dimension differs.
        """
        if not chunks:
            return

        if len(chunks) != embeddings.shape[0]:
            raise ValueError(
                f"Chunk count ({len(chunks)}) does not match embedding rows ({embeddings.shape[0]})."
            )

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension ({embeddings.shape[1]}) does not match index dimension ({self.dimension})."
            )

        # FAISS strictly requires float32 contiguous arrays
        contiguous_embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        self.index.add(contiguous_embeddings)
        self.chunks.extend(chunks)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[Chunk, float, int]]:
        """Retrieves top-K most similar chunks for a given query vector.

        Args:
            query_embedding: 1D or 2D vector for the query.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            List of tuples: (Chunk, cosine_similarity_score, rank_1_based).
        """
        if self.total_vectors == 0:
            return []

        # Ensure query is 2D float32 of shape (1, dimension)
        q_vec = np.ascontiguousarray(query_embedding, dtype=np.float32)
        if q_vec.ndim == 1:
            q_vec = q_vec.reshape(1, -1)

        if q_vec.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension ({q_vec.shape[1]}) does not match index dimension ({self.dimension})."
            )

        k = min(top_k, self.total_vectors)
        distances, indices = self.index.search(q_vec, k)

        results: List[Tuple[Chunk, float, int]] = []
        for rank_idx, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            results.append((chunk, float(dist), rank_idx))

        return results

    def reset(self) -> None:
        """Clears all indexed vectors and stored chunks."""
        import faiss

        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks.clear()

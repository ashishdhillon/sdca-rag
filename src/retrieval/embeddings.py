"""Sentence Transformers embedding generation and tokenizer extraction.

Maintains Ceteris Paribus controls:
1. Deterministic dense embeddings using a standard pre-trained checkpoint.
2. Direct access to the model's exact subword HuggingFace tokenizer.
3. L2 vector normalization so inner products equal cosine similarities.
"""

from typing import Any, List, Optional, Union
import numpy as np


class ModelTokenizer:
    """Tokenizer adapter wrapping a pre-trained SentenceTransformer/HuggingFace tokenizer.

    Implements the token counting protocol required across all chunking strategies
    (Fixed, Recursive, Sentence, SDCA) to guarantee tokenizer invariance.
    """

    def __init__(self, hf_tokenizer: Any):
        """Initializes with a HuggingFace tokenizer instance.

        Args:
            hf_tokenizer: The underlying HuggingFace AutoTokenizer or PreTrainedTokenizer.
        """
        self.hf_tokenizer = hf_tokenizer

    def count_tokens(self, text: str) -> int:
        """Counts exact subword tokens for a text snippet without special tokens.

        Args:
            text: Input string.

        Returns:
            Exact integer token count.
        """
        if not text or not text.strip():
            return 0
        return len(self.hf_tokenizer.encode(text, add_special_tokens=False))

    def tokenize(self, text: str) -> List[str]:
        """Returns list of token strings from the tokenizer.

        Args:
            text: Input string.

        Returns:
            List of subword token strings.
        """
        if not text or not text.strip():
            return []
        return self.hf_tokenizer.tokenize(text)

    def __call__(self, text: str) -> int:
        """Enables direct callable usage as a token counter."""
        return self.count_tokens(text)


class EmbeddingManager:
    """Manages dense vector embedding generation with Sentence Transformers.

    Enforces strict research control:
    - Fixed model weights across all comparisons
    - L2-normalized embeddings for exact cosine similarity in FAISS
    - Exposes model tokenizer for chunking invariance
    """

    DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: Optional[str] = None,
    ):
        """Initializes the embedding model.

        Args:
            model_name: HuggingFace model identifier.
            device: Optional device specification ('cpu', 'cuda', 'mps'). Defaults to auto.
        """
        # Imported lazily so non-embedding modules or tests without torch don't crash
        import logging
        logging.getLogger("transformers").setLevel(logging.ERROR)
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        try:
            self.model = SentenceTransformer(model_name, device=device, local_files_only=True)
        except Exception:
            self.model = SentenceTransformer(model_name, device=device)
        self.model.max_seq_length = 512
        self.dimension = (
            self.model.get_embedding_dimension()
            if hasattr(self.model, "get_embedding_dimension")
            else self.model.get_sentence_embedding_dimension()
        )
        self._tokenizer = ModelTokenizer(self.model.tokenizer)

    @property
    def tokenizer(self) -> ModelTokenizer:
        """Returns the model-matched tokenizer adapter."""
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        """Direct helper to count tokens using the model tokenizer."""
        return self._tokenizer.count_tokens(text)

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Encodes text or list of texts into dense vectors.

        Args:
            texts: Single text string or list of text strings.
            batch_size: Inference batch size.
            normalize_embeddings: Whether to L2-normalize vectors (required for cosine similarity).
            show_progress_bar: Whether to show progress bar during encoding.

        Returns:
            2D numpy array of shape (N, dimension) with dtype float32.
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize_embeddings,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )

        # Ensure float32 for FAISS compatibility
        return embeddings.astype(np.float32)

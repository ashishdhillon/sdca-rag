"""LangChain integration for SDCA (Structure-Aware Document Chunking Algorithm).

Provides SDCATextSplitter as a drop-in LangChain document transformer.
Preserves PDF geometry, tables, and heading breadcrumbs into LangChain Document objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from src.baselines.models import Chunk
from src.extraction.models import Document as SDCADocument
from src.extraction.pdf_parser import load_pdf
from src.sdca.v3.chunker import V3Options, chunk_sdca_stair

# Graceful import of LangChain Core
try:
    from langchain_core.documents import Document as LCDocument
    from langchain_core.documents.transformers import BaseDocumentTransformer
    _HAS_LANGCHAIN = True
except ImportError:
    _HAS_LANGCHAIN = False

    class BaseDocumentTransformer:  # type: ignore[no-redef]
        """Fallback base transformer when langchain_core is not installed."""
        pass

    @dataclass
    class LCDocument:  # type: ignore[no-redef]
        """Duck-typed LangChain Document fallback."""
        page_content: str
        metadata: Dict[str, Any] = field(default_factory=dict)

        def __repr__(self) -> str:
            preview = self.page_content[:60].replace("\n", " ")
            return f"Document(page_content='{preview}...', metadata={self.metadata})"


class SDCATextSplitter(BaseDocumentTransformer):
    """Drop-in LangChain Document Transformer powered by SDCA (STAIR).

    Unlike naive RecursiveCharacterTextSplitter, SDCATextSplitter preserves:
    1. Multi-column financial and experimental tables intact within chunks.
    2. Hierarchical section breadcrumbs prepended into retrieval representations.
    3. Structural heading bindings, eliminating orphaned clauses.

    Args:
        target_tokens: Desired target token capacity per chunk (default: 300).
        min_tokens: Minimum lower token floor before chunk merging (default: 120).
        max_tokens: Hard ceiling for chunk capacity (default: 420).
        use_retrieval_text: If True, sets page_content to retrieval_text
                           (with breadcrumbs). If False, sets page_content
                           to raw verbatim text and stores breadcrumbs in metadata.
        repair_hierarchy: Whether to deterministically repair section numbering (default: True).
        drop_nonbody: Whether to exclude front-matter blocks and references (default: True).
        size_floor: Token threshold below which small chunks are merged (default: 80).
        breadcrumb_depth: Number of trailing ancestral heading levels to keep (default: 2).
    """

    def __init__(
        self,
        target_tokens: int = 300,
        min_tokens: int = 120,
        max_tokens: int = 420,
        use_retrieval_text: bool = False,
        repair_hierarchy: bool = True,
        drop_nonbody: bool = True,
        size_floor: int = 80,
        breadcrumb_depth: int = 2,
        **kwargs: Any,
    ):
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.use_retrieval_text = use_retrieval_text
        self.options = V3Options(
            repair_hierarchy=repair_hierarchy,
            drop_nonbody=drop_nonbody,
            size_floor=size_floor,
            breadcrumb_depth=breadcrumb_depth,
        )
        self.kwargs = kwargs

    def _chunk_to_lc_doc(self, chunk: Chunk, default_metadata: Optional[Dict[str, Any]] = None) -> LCDocument:
        """Converts an internal SDCA Chunk into a standard LangChain Document."""
        meta = dict(default_metadata or {})
        chunk_meta = dict(chunk.metadata or {})

        meta.update({
            "chunk_id": chunk.chunk_id,
            "strategy": chunk.strategy,
            "section": chunk.section,
            "section_path": chunk_meta.get("v3_path") or chunk_meta.get("section_path") or [],
            "section_path_str": chunk_meta.get("section_path_str") or chunk.section or "",
            "page": chunk.page_start,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "token_count": chunk.token_count,
            "retrieval_text": getattr(chunk, "retrieval_text", None) or chunk.text,
        })

        content = chunk.retrieval_text if self.use_retrieval_text else chunk.text
        return LCDocument(page_content=content, metadata=meta)

    def split_pdf(self, pdf_path: Union[str, Path]) -> List[LCDocument]:
        """Loads and chunks a PDF directly using SDCA's layout and typography parser.

        Args:
            pdf_path: Path to the target PDF document.

        Returns:
            List of LangChain Document instances with full structural metadata.
        """
        path_obj = Path(pdf_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        sdca_doc = load_pdf(path_obj)
        chunks = chunk_sdca_stair(
            sdca_doc,
            target_tokens=self.target_tokens,
            min_tokens=self.min_tokens,
            max_tokens=self.max_tokens,
            options=self.options,
        )
        return [self._chunk_to_lc_doc(c, {"source": str(path_obj.resolve())}) for c in chunks]

    def split_text(self, text: str) -> List[str]:
        """Splits raw text string into structured chunk strings."""
        if not text.strip():
            return []
        chunks = chunk_sdca_stair(
            text,
            target_tokens=self.target_tokens,
            min_tokens=self.min_tokens,
            max_tokens=self.max_tokens,
            options=self.options,
        )
        if self.use_retrieval_text:
            return [getattr(c, "retrieval_text", None) or c.text for c in chunks]
        return [c.text for c in chunks]

    def create_documents(
        self,
        texts: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> List[LCDocument]:
        """Creates LangChain Documents from a list of texts and optional metadata."""
        out_docs: List[LCDocument] = []
        for i, text in enumerate(texts):
            base_meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            chunks = chunk_sdca_stair(
                text,
                target_tokens=self.target_tokens,
                min_tokens=self.min_tokens,
                max_tokens=self.max_tokens,
                options=self.options,
            )
            for c in chunks:
                out_docs.append(self._chunk_to_lc_doc(c, base_meta))
        return out_docs

    def split_documents(self, documents: Iterable[Any]) -> List[LCDocument]:
        """Splits LangChain Documents. If a document points to a valid source PDF,
        extracts layout-aware structure from the original PDF; otherwise chunks text."""
        result: List[LCDocument] = []
        for doc in documents:
            meta = getattr(doc, "metadata", {}) or {}
            source = meta.get("source")
            text = getattr(doc, "page_content", "") or getattr(doc, "text", "")

            # If the source points to a real PDF on disk, leverage full layout parser
            if source and Path(source).is_file() and str(source).lower().endswith(".pdf"):
                try:
                    pdf_docs = self.split_pdf(source)
                    # Merge any existing user metadata
                    for p_doc in pdf_docs:
                        p_doc.metadata.update({k: v for k, v in meta.items() if k not in p_doc.metadata})
                    result.extend(pdf_docs)
                    continue
                except Exception:
                    # Fallback to plain text splitting if PDF reading fails
                    pass

            # Fallback to structural string splitting
            chunks = chunk_sdca_stair(
                text,
                target_tokens=self.target_tokens,
                min_tokens=self.min_tokens,
                max_tokens=self.max_tokens,
                options=self.options,
            )
            for c in chunks:
                result.append(self._chunk_to_lc_doc(c, meta))

        return result

    def transform_documents(self, documents: Sequence[Any], **kwargs: Any) -> Sequence[LCDocument]:
        """LangChain BaseDocumentTransformer interface."""
        return self.split_documents(documents)

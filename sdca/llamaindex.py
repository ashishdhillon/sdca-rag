"""LlamaIndex integration for SDCA (Structure-Aware Document Chunking Algorithm).

Provides SDCANodeParser as a drop-in LlamaIndex node parser.
Preserves PDF geometry, tables, and heading breadcrumbs into LlamaIndex TextNode objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from src.baselines.models import Chunk
from src.extraction.models import Document as SDCADocument
from src.extraction.pdf_parser import load_pdf
from src.sdca.v3.chunker import V3Options, chunk_sdca_stair

# Graceful import of LlamaIndex Core
try:
    from llama_index.core.node_parser import NodeParser
    from llama_index.core.schema import TextNode, BaseNode
    _HAS_LLAMA_INDEX = True
except ImportError:
    _HAS_LLAMA_INDEX = False

    class NodeParser:  # type: ignore[no-redef]
        """Fallback base node parser when llama_index.core is not installed."""
        pass

    @dataclass
    class TextNode:  # type: ignore[no-redef]
        """Duck-typed LlamaIndex TextNode fallback."""
        text: str
        id_: str = ""
        metadata: Dict[str, Any] = field(default_factory=dict)
        excluded_embed_metadata_keys: List[str] = field(default_factory=list)
        excluded_llm_metadata_keys: List[str] = field(default_factory=list)

        @property
        def node_id(self) -> str:
            return self.id_

        def get_content(self, metadata_mode: Any = None) -> str:
            return self.text

        def __repr__(self) -> str:
            preview = self.text[:60].replace("\n", " ")
            return f"TextNode(id_='{self.id_}', text='{preview}...', metadata={self.metadata})"

    class BaseNode:  # type: ignore[no-redef]
        pass


if _HAS_LLAMA_INDEX:
    class SDCANodeParser(NodeParser):
        """Drop-in LlamaIndex Node Parser powered by SDCA (STAIR).

        Unlike sliding window SentenceSplitter, SDCANodeParser:
        1. Preserves multi-column financial and experimental tables within single TextNodes.
        2. Builds hierarchical breadcrumb representations in metadata and retrieval representations.
        3. Prevents context budget starvation by calibrating node capacity to 300 tokens.

        Args:
            target_tokens: Desired target token capacity per node (default: 300).
            min_tokens: Minimum lower token floor before node merging (default: 120).
            max_tokens: Hard ceiling for node capacity (default: 420).
            use_retrieval_text: If True, sets node.text to retrieval_text (with breadcrumbs).
            repair_hierarchy: Whether to deterministically repair section numbering (default: True).
            drop_nonbody: Whether to exclude front-matter blocks and references (default: True).
            size_floor: Token threshold below which small chunks are merged (default: 80).
            breadcrumb_depth: Number of trailing ancestral heading levels to keep (default: 2).
        """

        target_tokens: int = 300
        min_tokens: int = 120
        max_tokens: int = 420
        use_retrieval_text: bool = False
        repair_hierarchy: bool = True
        drop_nonbody: bool = True
        size_floor: int = 80
        breadcrumb_depth: int = 2

        @property
        def options(self) -> V3Options:
            return V3Options(
                repair_hierarchy=self.repair_hierarchy,
                drop_nonbody=self.drop_nonbody,
                size_floor=self.size_floor,
                breadcrumb_depth=self.breadcrumb_depth,
            )

        def _chunk_to_text_node(self, chunk: Chunk, default_metadata: Optional[Dict[str, Any]] = None) -> TextNode:
            meta = dict(default_metadata or {})
            chunk_meta = dict(chunk.metadata or {})

            meta.update({
                "chunk_id": chunk.chunk_id,
                "strategy": chunk.strategy,
                "section": chunk.section,
                "section_path": chunk_meta.get("v3_path") or chunk_meta.get("section_path") or [],
                "section_path_str": chunk_meta.get("section_path_str") or chunk.section or "",
                "page_label": str(chunk.page_start),
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "token_count": chunk.token_count,
                "retrieval_text": getattr(chunk, "retrieval_text", None) or chunk.text,
            })

            content = chunk.retrieval_text if self.use_retrieval_text else chunk.text
            return TextNode(
                text=content,
                id_=chunk.chunk_id,
                metadata=meta,
            )

        def parse_pdf(self, pdf_path: Union[str, Path]) -> List[TextNode]:
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
            return [
                self._chunk_to_text_node(
                    c, {"file_name": path_obj.name, "file_path": str(path_obj.resolve())}
                )
                for c in chunks
            ]

        def _parse_nodes(
            self,
            nodes: Sequence[BaseNode],
            show_progress: bool = False,
            **kwargs: Any,
        ) -> List[BaseNode]:
            out_nodes: List[BaseNode] = []
            for n in nodes:
                meta = dict(getattr(n, "metadata", {}) or {})
                file_path = meta.get("file_path") or meta.get("source")
                text = n.get_content() if hasattr(n, "get_content") else getattr(n, "text", "")

                if file_path and Path(file_path).is_file() and str(file_path).lower().endswith(".pdf"):
                    try:
                        pdf_nodes = self.parse_pdf(file_path)
                        for pn in pdf_nodes:
                            pn.metadata.update({k: v for k, v in meta.items() if k not in pn.metadata})
                        out_nodes.extend(pdf_nodes)
                        continue
                    except Exception:
                        pass

                chunks = chunk_sdca_stair(
                    text,
                    target_tokens=self.target_tokens,
                    min_tokens=self.min_tokens,
                    max_tokens=self.max_tokens,
                    options=self.options,
                )
                for c in chunks:
                    out_nodes.append(self._chunk_to_text_node(c, meta))

            return out_nodes

else:
    class SDCANodeParser:  # type: ignore[no-redef]
        """Fallback SDCANodeParser when llama_index.core is not installed."""

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

        def _chunk_to_text_node(self, chunk: Chunk, default_metadata: Optional[Dict[str, Any]] = None) -> TextNode:
            meta = dict(default_metadata or {})
            chunk_meta = dict(chunk.metadata or {})

            meta.update({
                "chunk_id": chunk.chunk_id,
                "strategy": chunk.strategy,
                "section": chunk.section,
                "section_path": chunk_meta.get("v3_path") or chunk_meta.get("section_path") or [],
                "section_path_str": chunk_meta.get("section_path_str") or chunk.section or "",
                "page_label": str(chunk.page_start),
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "token_count": chunk.token_count,
                "retrieval_text": getattr(chunk, "retrieval_text", None) or chunk.text,
            })

            content = chunk.retrieval_text if self.use_retrieval_text else chunk.text
            return TextNode(
                text=content,
                id_=chunk.chunk_id,
                metadata=meta,
            )

        def parse_pdf(self, pdf_path: Union[str, Path]) -> List[TextNode]:
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
            return [
                self._chunk_to_text_node(
                    c, {"file_name": path_obj.name, "file_path": str(path_obj.resolve())}
                )
                for c in chunks
            ]

        def get_nodes_from_documents(self, documents: Sequence[Any], **kwargs: Any) -> List[TextNode]:
            nodes: List[TextNode] = []
            for doc in documents:
                meta = getattr(doc, "metadata", {}) or getattr(doc, "extra_info", {}) or {}
                file_path = meta.get("file_path") or meta.get("source")
                text = getattr(doc, "text", "") or getattr(doc, "page_content", "")

                if file_path and Path(file_path).is_file() and str(file_path).lower().endswith(".pdf"):
                    try:
                        pdf_nodes = self.parse_pdf(file_path)
                        for pn in pdf_nodes:
                            pn.metadata.update({k: v for k, v in meta.items() if k not in pn.metadata})
                        nodes.extend(pdf_nodes)
                        continue
                    except Exception:
                        pass

                chunks = chunk_sdca_stair(
                    text,
                    target_tokens=self.target_tokens,
                    min_tokens=self.min_tokens,
                    max_tokens=self.max_tokens,
                    options=self.options,
                )
                for c in chunks:
                    nodes.append(self._chunk_to_text_node(c, meta))

            return nodes

        def build_nodes_from_documents(self, documents: Sequence[Any], **kwargs: Any) -> List[TextNode]:
            return self.get_nodes_from_documents(documents, **kwargs)

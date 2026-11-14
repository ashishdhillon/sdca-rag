"""SDCA V3 chunker.

Motivation (see docs/V3_DESIGN.md): inspection of V2 output on the three benchmark
PDFs showed (a) wrong breadcrumbs, e.g. "4 Experiments" nested under "3.2 Fine-tuning"
and the paper title acting as ancestor of every section; (b) reference lists and
title/author blocks being indexed as content; (c) chunks of 11-30 tokens that waste
top-k slots. V3 addresses each with a separate, switchable step.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from src.baselines.models import Chunk
from src.baselines.tokenization import get_token_counter
from src.extraction.models import Document
from src.sdca.v2.chunker import chunk_sdca_v2

# "4", "3.2", "A.1", "I" followed by a space/period and a title.
_NUM_HEAD = re.compile(r"^\s*((?:\d+|[A-Z])(?:\.\d+)*)[.\s]+(\S.*)$", re.S)
_REF_HEAD = re.compile(r"^\s*(references|bibliography)\b", re.I)
_FRONT_STOP = re.compile(r"^\s*(abstract|(1|i)[.\s]+\S|introduction)\b", re.I)


@dataclass(frozen=True)
class V3Options:
    repair_hierarchy: bool = True      # rebuild breadcrumbs from heading numbering
    drop_nonbody: bool = True          # drop title block and reference list from the index
    size_floor: int = 120              # merge chunks below this many tokens (0 disables)
    breadcrumb_depth: int = 2          # how many trailing path levels go in retrieval_text


def _heading_depth(heading: Optional[str]) -> Tuple[int, str]:
    """Return (depth, title) from a heading. Unnumbered headings are depth 1."""
    if not heading:
        return 1, ""
    first_line = heading.strip().split("\n", 1)[0].strip()
    m = _NUM_HEAD.match(first_line)
    if m:
        return m.group(1).count(".") + 1, first_line
    return 1, first_line


_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def is_reference_like(text: str, token_count: int, min_density: float = 1.2) -> bool:
    """Citation-list heuristic: publication years per 100 tokens. Used for ALL
    strategies in the ablation so that V3 gets no credit for index hygiene
    that any chunker could apply."""
    if token_count < 40:
        return False
    return len(_YEAR.findall(text)) / token_count * 100 >= min_density


def _classify(chunks: List[Chunk]) -> List[str]:
    """Label each chunk 'front', 'body' or 'refs'.

    'refs' starts at a References heading and continues only while chunks look
    like citation lists, so appendices that follow the bibliography stay 'body'.
    """
    kinds = ["body"] * len(chunks)
    # Front matter: leading page-1 chunks before the abstract/introduction begins.
    for i, c in enumerate(chunks):
        sec = (c.section or "").strip()
        if _FRONT_STOP.match(sec) or _FRONT_STOP.match(c.text.strip()):
            break
        if c.page_start == 1 and c.token_count < 200:
            kinds[i] = "front"
        else:
            break
    in_refs = False
    for i, c in enumerate(chunks):
        if _REF_HEAD.match((c.section or "").strip()):
            in_refs = True
            kinds[i] = "refs"
        elif in_refs:
            if is_reference_like(c.text, c.token_count):
                kinds[i] = "refs"
            else:
                in_refs = False
    return kinds


def _repair_paths(chunks: List[Chunk]) -> List[List[str]]:
    """Rebuild each chunk's heading path from numbering depth, ignoring V2's stack."""
    stack: List[Tuple[int, str]] = []
    paths: List[List[str]] = []
    for c in chunks:
        depth, title = _heading_depth(c.section)
        if title:
            while stack and stack[-1][0] >= depth:
                stack.pop()
            stack.append((depth, title))
        paths.append([t for _, t in stack])
    return paths


def _merge(a: Chunk, b: Chunk, counter: Callable[[str], int]) -> Chunk:
    text = f"{a.text}\n\n{b.text}"
    meta = dict(a.metadata)
    meta["merged_from"] = meta.get("merged_from", [a.chunk_id]) + [b.chunk_id]
    return replace(a, text=text, page_end=max(a.page_end, b.page_end),
                   token_count=counter(text), metadata=meta, retrieval_text=None)


def chunk_sdca_v3(
    document: Union[Document, str],
    target_tokens: int = 400,
    min_tokens: int = 200,
    max_tokens: int = 600,
    tokenizer: Optional[Any] = None,
    options: Optional[V3Options] = None,
) -> List[Chunk]:
    opts = options or V3Options()
    counter = get_token_counter(tokenizer)
    base = chunk_sdca_v2(document, target_tokens=target_tokens, min_tokens=min_tokens,
                         max_tokens=max_tokens, tokenizer=tokenizer)
    if not base:
        return []

    kinds = _classify(base)
    paths = _repair_paths(base) if opts.repair_hierarchy else [
        list(c.metadata.get("section_path") or []) for c in base]

    items: List[Chunk] = []
    for c, k, p in zip(base, kinds, paths):
        if opts.drop_nonbody and k != "body":
            continue
        meta = dict(c.metadata)
        meta.update({"kind": k, "v3_path": p, "v2_chunk_id": c.chunk_id})
        items.append(replace(c, metadata=meta))

    # Safeguard: if dropping non-body removes 100% of chunks (e.g. single-page short document), preserve base
    if not items and base:
        items = [replace(c, metadata={**c.metadata, "kind": "body", "v3_path": p, "v2_chunk_id": c.chunk_id})
                 for c, p in zip(base, paths)]

    # Size floor: merge a too-small chunk with its neighbour when the result fits.
    if opts.size_floor > 0:
        out: List[Chunk] = []
        for c in items:
            if out:
                prev = out[-1]
                small = c.token_count < opts.size_floor or prev.token_count < opts.size_floor
                fits = prev.token_count + c.token_count <= max_tokens
                if small and fits and prev.metadata["kind"] == c.metadata["kind"]:
                    out[-1] = _merge(prev, c, counter)
                    continue
            out.append(c)
        items = out

    final: List[Chunk] = []
    for idx, c in enumerate(items):
        path = c.metadata["v3_path"]
        crumb = " > ".join(path[-opts.breadcrumb_depth:]) if opts.breadcrumb_depth > 0 else ""
        rt = f"[Section: {crumb}]\n\n{c.text}" if crumb else c.text
        meta = dict(c.metadata)
        meta["section_path_str"] = " > ".join(path)
        meta["retrieval_text"] = rt
        final.append(replace(c, chunk_id=f"sdca_v3_{idx}", strategy="sdca_v3",
                             metadata=meta, retrieval_text=rt))
    return final


def chunk_sdca_stair(
    document: Union[Document, str],
    target_tokens: int = 300,
    min_tokens: int = 120,
    max_tokens: int = 420,
    tokenizer: Optional[Any] = None,
    options: Optional[V3Options] = None,
) -> List[Chunk]:
    """STAIR-adapted SDCA chunker.
    
    Optimized for fixed-budget RAG contexts: compact target chunk size (300 tokens)
    prevents context budget starvation, while hierarchical breadcrumbs and non-body
    filtering eliminate front-matter noise.
    """
    opts = options or V3Options(repair_hierarchy=True, drop_nonbody=True, size_floor=80, breadcrumb_depth=2)
    return chunk_sdca_v3(document, target_tokens=target_tokens, min_tokens=min_tokens,
                          max_tokens=max_tokens, tokenizer=tokenizer, options=opts)


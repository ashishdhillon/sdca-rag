"""SDCA V2 (Structure-Aware Document Chunking Algorithm V2) implementation.

Key Improvements in SDCA V2:
1. Heading-Content Binding: Avoids standalone heading-only chunks by binding
   umbrella headings into the hierarchical section path and attaching immediate
   headings to body content.
2. Hierarchical Section Context: Preserves parent heading, section path breadcrumbs,
   and hierarchy level in chunk metadata.
3. Structure-Aware Retrieval Text: Constructs an explicit retrieval representation
   (`chunk.retrieval_text`) prepended with the ancestral section hierarchy path,
   maximizing dense vector matching while preserving clean verbatim text in `chunk.text`.
4. Adaptive Small-Chunk Handling: Merges under-sized chunks with adjacent compatible
   subsections sharing the same parent hierarchy, while strictly preserving major
   Level 1 chapter/section boundaries.
"""

from typing import Any, Callable, List, Optional, Tuple, Union

from src.baselines.models import Chunk
from src.baselines.sentence import segment_sentences
from src.baselines.tokenization import get_token_counter
from src.extraction.models import Document, Page, TextBlock, TextSpan
from src.sdca.chunker import _split_oversized_paragraph
from src.sdca.structure import NUMBERED_HEADING_PATTERN, Paragraph
from src.sdca.v2.structure import (
    HeadingDetectorV2,
    SectionV2,
    detect_document_structure_v2,
)


def _build_synthetic_document_v2(text: str) -> Document:
    """Wraps plain text string into a synthetic Document for uniform SDCA V2 processing."""
    raw_blocks = text.strip().split("\n\n")
    blocks: List[TextBlock] = []

    for idx, b_text in enumerate(raw_blocks):
        b_clean = b_text.strip()
        if not b_clean:
            continue

        is_num = bool(NUMBERED_HEADING_PATTERN.match(b_clean))
        is_short = len(b_clean.split()) <= 6 and not b_clean.endswith(".")
        is_hd = is_num or is_short
        font_sz = 14.0 if is_hd else 10.0
        flags = 4 if is_hd else 0

        span = TextSpan(
            text=b_clean,
            bbox=(50.0, 50.0 + idx * 30.0, 400.0, 70.0 + idx * 30.0),
            font="Helvetica-Bold" if flags else "Helvetica",
            font_size=font_sz,
            flags=flags,
        )
        blocks.append(
            TextBlock(
                block_id=idx,
                bbox=span.bbox,
                text=b_clean,
                block_type=0,
                spans=[span],
            )
        )

    page = Page(page_number=1, width=595.0, height=842.0, blocks=blocks)
    return Document(source_path="<in-memory-text>", page_count=1, pages=[page])


def chunk_sdca_v2(
    document: Union[Document, str],
    target_tokens: int = 400,
    min_tokens: int = 200,
    max_tokens: int = 600,
    tokenizer: Optional[Any] = None,
) -> List[Chunk]:
    """Applies SDCA V2 with hierarchical section context and structure-aware retrieval representations.

    Args:
        document: Extracted Document hierarchy from Phase 1 or raw text string.
        target_tokens: Desired target token capacity per chunk. Defaults to 400.
        min_tokens: Lower preferred token boundary. Defaults to 200.
        max_tokens: Upper hard token boundary. Defaults to 600.
        tokenizer: Optional custom tokenizer or token count callable.

    Returns:
        List of structured Chunk instances containing both clean display text and
        structure-aware retrieval representations (`chunk.retrieval_text`).

    Raises:
        ValueError: If token constraints violate 0 < min_tokens <= target_tokens <= max_tokens.
    """
    if min_tokens <= 0:
        raise ValueError(f"min_tokens must be positive, got {min_tokens}")
    if target_tokens < min_tokens:
        raise ValueError(
            f"target_tokens ({target_tokens}) must be >= min_tokens ({min_tokens})"
        )
    if max_tokens < target_tokens:
        raise ValueError(
            f"max_tokens ({max_tokens}) must be >= target_tokens ({target_tokens})"
        )

    if isinstance(document, str):
        if not document.strip():
            return []
        document = _build_synthetic_document_v2(document)

    token_counter = get_token_counter(tokenizer)

    # 1. Detect document hierarchy with ancestral paths
    sections = detect_document_structure_v2(document, tokenizer=tokenizer)
    if not sections:
        return []

    # 2. Assemble chunks within each section
    raw_chunks: List[Dict[str, Any]] = []

    for sec in sections:
        if not sec.paragraphs:
            # Under V2, umbrella headings without body text are absorbed into the hierarchy stack
            continue

        # Split any oversized paragraphs at sentence boundaries
        normalized_paras: List[Paragraph] = []
        for p in sec.paragraphs:
            normalized_paras.extend(
                _split_oversized_paragraph(p, max_tokens=max_tokens, token_counter=token_counter)
            )

        # Heading binding: immediate heading attached to first chunk of section
        is_first_chunk = True
        curr_paras: List[Paragraph] = []
        curr_tokens = 0
        heading_prefix = f"{sec.heading}\n\n" if sec.heading else ""
        heading_tokens = token_counter(sec.heading) if sec.heading else 0

        for p in normalized_paras:
            p_tok = p.token_count
            added_prefix_tok = heading_tokens if (is_first_chunk and not curr_paras) else 0
            cand_tokens = curr_tokens + p_tok + added_prefix_tok

            if not curr_paras:
                curr_paras.append(p)
                curr_tokens = p_tok + added_prefix_tok
            elif cand_tokens <= max_tokens:
                curr_paras.append(p)
                curr_tokens = cand_tokens
            else:
                # Emit current accumulated chunk
                body_text = "\n\n".join(cp.text for cp in curr_paras)
                chunk_text = f"{heading_prefix}{body_text}" if (is_first_chunk and heading_prefix) else body_text
                p_start = curr_paras[0].page_number
                p_end = curr_paras[-1].page_number
                c_tok = token_counter(chunk_text)

                raw_chunks.append({
                    "text": chunk_text,
                    "page_start": p_start,
                    "page_end": p_end,
                    "section": sec.heading,
                    "parent_heading": sec.parent_heading,
                    "section_path": sec.section_path,
                    "section_path_str": sec.section_path_str,
                    "level": sec.level,
                    "token_count": c_tok,
                })

                is_first_chunk = False
                curr_paras = [p]
                curr_tokens = p_tok

        if curr_paras:
            body_text = "\n\n".join(cp.text for cp in curr_paras)
            chunk_text = f"{heading_prefix}{body_text}" if (is_first_chunk and heading_prefix) else body_text
            p_start = curr_paras[0].page_number
            p_end = curr_paras[-1].page_number
            c_tok = token_counter(chunk_text)

            raw_chunks.append({
                "text": chunk_text,
                "page_start": p_start,
                "page_end": p_end,
                "section": sec.heading,
                "parent_heading": sec.parent_heading,
                "section_path": sec.section_path,
                "section_path_str": sec.section_path_str,
                "level": sec.level,
                "token_count": c_tok,
            })

    if not raw_chunks:
        return []

    # 3. Small-chunk handling with hierarchical awareness
    # Merge under-sized chunks (< min_tokens) when:
    # - In the same section, OR
    # - Sharing the same parent heading in the hierarchy tree (compatible sub-sections), OR
    # - Preceded by a headless preamble.
    # Strict Invariant: Major Level 1 sections (level == 1) are never merged across boundaries.
    merged_raw: List[Dict[str, Any]] = []

    for item in raw_chunks:
        if not merged_raw:
            merged_raw.append(item)
            continue

        prev = merged_raw[-1]
        c_tok = item["token_count"]
        prev_tok = prev["token_count"]

        # Case A: Same exact section
        can_merge_same = (
            prev["section"] == item["section"]
            and (c_tok < min_tokens or prev_tok < min_tokens)
            and (prev_tok + c_tok <= max_tokens)
        )

        # Case B: Compatible sibling subsections under the same parent heading
        can_merge_siblings = (
            prev.get("parent_heading") is not None
            and prev.get("parent_heading") == item.get("parent_heading")
            and prev["level"] > 1
            and item["level"] > 1
            and (c_tok < min_tokens or prev_tok < min_tokens)
            and (prev_tok + c_tok <= max_tokens)
        )

        # Case C: Preamble merging with subsequent content
        can_merge_preamble = (
            prev["section"] is None
            and prev_tok < min_tokens
            and (prev_tok + c_tok <= max_tokens)
        )

        if can_merge_same or can_merge_siblings or can_merge_preamble:
            comb_text = f"{prev['text']}\n\n{item['text']}"
            comb_tok = token_counter(comb_text)

            # Sibling merge keeps common parent or unified path
            if can_merge_siblings:
                active_sec = prev["section"]
                active_path = prev["section_path"]
                active_path_str = prev["section_path_str"]
            elif prev["section"] is None:
                active_sec = item["section"]
                active_path = item["section_path"]
                active_path_str = item["section_path_str"]
            else:
                active_sec = prev["section"]
                active_path = prev["section_path"]
                active_path_str = prev["section_path_str"]

            merged_raw[-1] = {
                "text": comb_text,
                "page_start": prev["page_start"],
                "page_end": item["page_end"],
                "section": active_sec,
                "parent_heading": prev.get("parent_heading") or item.get("parent_heading"),
                "section_path": active_path,
                "section_path_str": active_path_str,
                "level": min(prev["level"], item["level"]),
                "token_count": comb_tok,
            }
        else:
            merged_raw.append(item)

    # 4. Construct final Chunk instances with Structure-Aware Retrieval Text
    final_chunks: List[Chunk] = []

    for idx, item in enumerate(merged_raw):
        clean_text = item["text"].strip()
        path_str = item["section_path_str"]

        # Build retrieval representation
        if path_str and path_str != "Preamble" and path_str != "General":
            retrieval_text = f"[Section: {path_str}]\n\n{clean_text}"
        else:
            retrieval_text = clean_text

        retrieval_tokens = token_counter(retrieval_text)

        metadata = {
            "target_tokens": target_tokens,
            "min_tokens": min_tokens,
            "max_tokens": max_tokens,
            "parent_heading": item.get("parent_heading"),
            "section_path": item.get("section_path", []),
            "section_path_str": path_str,
            "hierarchy_level": item.get("level", 1),
            "retrieval_text": retrieval_text,
            "retrieval_tokens": retrieval_tokens,
        }

        final_chunks.append(
            Chunk(
                chunk_id=f"sdca_v2_{idx}",
                text=clean_text,
                page_start=item["page_start"],
                page_end=item["page_end"],
                token_count=item["token_count"],
                strategy="sdca_v2",
                section=item["section"],
                metadata=metadata,
                retrieval_text=retrieval_text,
            )
        )

    return final_chunks

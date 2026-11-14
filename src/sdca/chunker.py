"""SDCA (Structure-Aware Document Chunking Algorithm) implementation.

Assembles deterministic, layout-aware chunks by preserving:
1. Section and heading boundaries
2. Paragraph boundaries
3. Sentence boundaries (as splitting fallback for oversized content)
4. Word boundaries (never splitting words)

Does not use embeddings, semantic similarity, or LLMs.
"""

from typing import Any, Callable, List, Optional, Tuple, Union

from src.baselines.models import Chunk
from src.baselines.sentence import segment_sentences
from src.baselines.tokenization import get_token_counter
from src.extraction.models import Document, Page, TextBlock, TextSpan
from src.sdca.structure import (
    NUMBERED_HEADING_PATTERN,
    Paragraph,
    Section,
    detect_document_structure,
)


def _split_oversized_paragraph(
    paragraph: Paragraph,
    max_tokens: int,
    token_counter: Callable[[str], int],
) -> List[Paragraph]:
    """Decomposes an oversized paragraph at sentence boundaries into compliant Paragraph units.

    If an individual sentence exceeds max_tokens, falls back safely to word boundaries
    without intentionally splitting words.
    """
    if paragraph.token_count <= max_tokens:
        return [paragraph]

    sentences = segment_sentences(paragraph.text)
    if not sentences:
        return [paragraph]

    units: List[Paragraph] = []
    current_sentences: List[str] = []
    current_tokens = 0

    for sent_text, _, _ in sentences:
        s_tokens = token_counter(sent_text)

        # Edge case: An individual sentence exceeds max_tokens
        if s_tokens > max_tokens:
            # First flush any accumulated sentences
            if current_sentences:
                combined_text = " ".join(current_sentences)
                units.append(
                    Paragraph(
                        text=combined_text,
                        page_number=paragraph.page_number,
                        block_id=paragraph.block_id,
                        token_count=token_counter(combined_text),
                    )
                )
                current_sentences = []
                current_tokens = 0

            # Split oversized sentence at word boundaries
            words = sent_text.split()
            word_group: List[str] = []
            word_tokens = 0
            for w in words:
                w_tok = token_counter(w)
                if word_tokens + w_tok > max_tokens and word_group:
                    w_text = " ".join(word_group)
                    units.append(
                        Paragraph(
                            text=w_text,
                            page_number=paragraph.page_number,
                            block_id=paragraph.block_id,
                            token_count=token_counter(w_text),
                        )
                    )
                    word_group = [w]
                    word_tokens = w_tok
                else:
                    word_group.append(w)
                    word_tokens += w_tok

            if word_group:
                w_text = " ".join(word_group)
                units.append(
                    Paragraph(
                        text=w_text,
                        page_number=paragraph.page_number,
                        block_id=paragraph.block_id,
                        token_count=token_counter(w_text),
                    )
                )
            continue

        # Normal sentence grouping
        if current_tokens + s_tokens > max_tokens and current_sentences:
            combined_text = " ".join(current_sentences)
            units.append(
                Paragraph(
                    text=combined_text,
                    page_number=paragraph.page_number,
                    block_id=paragraph.block_id,
                    token_count=token_counter(combined_text),
                )
            )
            current_sentences = [sent_text]
            current_tokens = s_tokens
        else:
            current_sentences.append(sent_text)
            current_tokens += s_tokens

    if current_sentences:
        combined_text = " ".join(current_sentences)
        units.append(
            Paragraph(
                text=combined_text,
                page_number=paragraph.page_number,
                block_id=paragraph.block_id,
                token_count=token_counter(combined_text),
            )
        )

    return units


def _build_synthetic_document(text: str) -> Document:
    """Wraps plain text string into a synthetic Document for uniform SDCA processing."""
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


def chunk_sdca(
    document: Union[Document, str],
    target_tokens: int = 400,
    min_tokens: int = 200,
    max_tokens: int = 600,
    tokenizer: Optional[Any] = None,
) -> List[Chunk]:
    """Applies the Structure-Aware Document Chunking Algorithm (SDCA) to a document.

    Args:
        document: Extracted Document hierarchy from Phase 1 or raw text string.
        target_tokens: Desired target token capacity per chunk. Defaults to 400.
        min_tokens: Lower preferred token boundary. Defaults to 200.
        max_tokens: Upper hard token boundary. Defaults to 600.
        tokenizer: Optional custom tokenizer or token count callable.

    Returns:
        List of structured Chunk instances preserving document headings and hierarchy.

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
        document = _build_synthetic_document(document)

    token_counter = get_token_counter(tokenizer)

    # 1. Structure Detection: Extract sections, headings, and paragraphs
    raw_sections = detect_document_structure(document, tokenizer=tokenizer)
    if not raw_sections:
        return []

    # 2. Merge orphaned headings or preambles where appropriate
    sections: List[Section] = []
    for sec in raw_sections:
        if not sec.paragraphs and sec.heading:
            # Standalone heading with no paragraphs: buffer it to prepend to next section
            if sections and not sections[-1].paragraphs:
                # Merge multiple successive heading lines
                sections[-1].heading = f"{sections[-1].heading} - {sec.heading}"
            else:
                sections.append(sec)
        else:
            if sections and not sections[-1].paragraphs and sections[-1].heading:
                # Prepend pending heading context to this section
                sec.heading = f"{sections[-1].heading} - {sec.heading}" if sec.heading else sections[-1].heading
                sections.pop()
            sections.append(sec)

    # 3. Assemble chunks within each section honoring structure
    raw_chunks: List[Tuple[str, int, int, Optional[str], int]] = []
    # Tuples: (text, page_start, page_end, section_name, token_count)

    for sec in sections:
        if not sec.paragraphs:
            if sec.heading:
                # Section with only a heading and no body text at all
                h_tok = token_counter(sec.heading)
                raw_chunks.append((sec.heading, sec.page_start, sec.page_end, sec.heading, h_tok))
            continue

        # Normalize any oversized paragraphs at sentence boundaries
        normalized_paras: List[Paragraph] = []
        for p in sec.paragraphs:
            normalized_paras.extend(
                _split_oversized_paragraph(p, max_tokens=max_tokens, token_counter=token_counter)
            )

        # Assemble normalized paragraphs into chunks
        is_first_chunk_of_section = True
        curr_paras: List[Paragraph] = []
        curr_tokens = 0
        heading_prefix = f"{sec.heading}\n\n" if sec.heading else ""
        heading_tokens = token_counter(sec.heading) if sec.heading else 0

        for p in normalized_paras:
            p_tok = p.token_count
            added_prefix_tok = heading_tokens if (is_first_chunk_of_section and not curr_paras) else 0
            cand_tokens = curr_tokens + p_tok + added_prefix_tok

            if not curr_paras:
                curr_paras.append(p)
                curr_tokens = p_tok + added_prefix_tok
            elif cand_tokens <= max_tokens:
                # Prefer completing the paragraph if it fits within max_tokens
                curr_paras.append(p)
                curr_tokens = cand_tokens
            else:
                # Emitting current chunk to avoid exceeding max_tokens
                body_text = "\n\n".join(cp.text for cp in curr_paras)
                if is_first_chunk_of_section and heading_prefix:
                    chunk_text = f"{heading_prefix}{body_text}"
                else:
                    chunk_text = body_text

                p_start = curr_paras[0].page_number
                p_end = curr_paras[-1].page_number
                c_tok = token_counter(chunk_text)
                raw_chunks.append((chunk_text, p_start, p_end, sec.heading, c_tok))

                # Reset for next chunk in same section
                is_first_chunk_of_section = False
                curr_paras = [p]
                curr_tokens = p_tok

        if curr_paras:
            body_text = "\n\n".join(cp.text for cp in curr_paras)
            if is_first_chunk_of_section and heading_prefix:
                chunk_text = f"{heading_prefix}{body_text}"
            else:
                chunk_text = body_text

            p_start = curr_paras[0].page_number
            p_end = curr_paras[-1].page_number
            c_tok = token_counter(chunk_text)
            raw_chunks.append((chunk_text, p_start, p_end, sec.heading, c_tok))

    if not raw_chunks:
        return []

    # 4. Small chunk handling:
    # Merge under-sized chunks with adjacent compatible content within the same section,
    # or merge headless preambles with following content if sum <= max_tokens.
    # Structural boundaries between distinct major sections are preserved.
    merged_raw: List[Tuple[str, int, int, Optional[str], int]] = []

    for item in raw_chunks:
        c_text, p_start, p_end, s_name, c_tok = item

        if not merged_raw:
            merged_raw.append(item)
            continue

        prev_text, prev_start, prev_end, prev_sec, prev_tok = merged_raw[-1]

        # Case A: Same section tail chunk is below min_tokens and fits within max_tokens
        can_merge_same_section = (
            prev_sec == s_name
            and (c_tok < min_tokens or prev_tok < min_tokens)
            and (prev_tok + c_tok <= max_tokens)
        )

        # Case B: Previous chunk was headless preamble and fits within max_tokens
        can_merge_preamble = (
            prev_sec is None
            and prev_tok < min_tokens
            and (prev_tok + c_tok <= max_tokens)
        )

        if can_merge_same_section or can_merge_preamble:
            comb_text = f"{prev_text}\n\n{c_text}"
            comb_tok = token_counter(comb_text)
            new_sec = s_name if prev_sec is None else prev_sec
            merged_raw[-1] = (comb_text, prev_start, p_end, new_sec, comb_tok)
        else:
            merged_raw.append(item)

    # 5. Convert to final Chunk instances
    final_chunks: List[Chunk] = []
    for idx, (text, p_start, p_end, section_name, tok_cnt) in enumerate(merged_raw):
        final_chunks.append(
            Chunk(
                chunk_id=f"sdca_{idx}",
                text=text.strip(),
                page_start=p_start,
                page_end=p_end,
                token_count=tok_cnt,
                strategy="sdca",
                section=section_name,
                metadata={
                    "target_tokens": target_tokens,
                    "min_tokens": min_tokens,
                    "max_tokens": max_tokens,
                },
            )
        )

    return final_chunks

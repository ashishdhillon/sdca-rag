from src.baselines.models import Chunk
from src.retrieval.hybrid import BM25, rrf, structure_guided_rrf
from src.sdca.v3 import chunk_sdca_stair
from src.sdca.v3.chunker import (V3Options, _classify, _heading_depth,
                                 _repair_paths, is_reference_like)


def mk(i, sec, text, tok, page=2):
    return Chunk(chunk_id=f"c{i}", text=text, page_start=page, page_end=page,
                 token_count=tok, strategy="sdca_v2", section=sec)


def test_heading_depth_from_numbering():
    assert _heading_depth("4 Experiments")[0] == 1
    assert _heading_depth("3.2 Fine-tuning BERT")[0] == 2
    assert _heading_depth("Abstract")[0] == 1


def test_repair_paths_pops_siblings_and_ignores_title():
    cs = [mk(0, "Abstract", "x", 50), mk(1, "3 Method", "x", 50),
          mk(2, "3.2 Fine-tuning", "x", 50), mk(3, "4 Experiments", "x", 50)]
    paths = _repair_paths(cs)
    assert paths[2] == ["3 Method", "3.2 Fine-tuning"]
    assert paths[3] == ["4 Experiments"]          # V2 nested this under 3.2
    assert paths[1] == ["3 Method"]               # 'Abstract' is not an ancestor


def test_reference_filter_keeps_appendix_after_refs():
    refs = " ".join(f"A. Author. Title. Journal, {1990+i%30}." for i in range(40))
    cs = [mk(0, "References", refs, 300), mk(1, "A Details", "plain prose " * 100, 200)]
    assert _classify(cs) == ["refs", "body"]
    assert is_reference_like(refs, 300) and not is_reference_like("plain prose " * 100, 200)


def test_bm25_and_rrf():
    docs = ["attention is all you need", "bert masked language model", "dense passage retrieval"]
    s = BM25(docs).scores("masked language model")
    assert s.index(max(s)) == 1
    fused = rrf([s, [0.0, 1.0, 0.5]])
    assert fused.index(max(fused)) == 1


def test_structure_guided_rrf():
    dense_scores = [0.1, 0.9, 0.5]
    bm25_scores = [0.2, 0.8, 0.4]
    sec_scores = [0.1, 0.8, 0.3]
    # Without section guidance, item 1 wins
    fused_plain = structure_guided_rrf(dense_scores, bm25_scores, alpha_sec=0.0)
    assert fused_plain.index(max(fused_plain)) == 1
    # With section boost aligned with relevant section, item 1 wins by even wider margin
    fused_boosted = structure_guided_rrf(dense_scores, bm25_scores, sec_scores, alpha_sec=0.003)
    assert fused_boosted[1] > fused_plain[1]
    assert fused_boosted.index(max(fused_boosted)) == 1



"""Dependency-free BM25 and rank fusion for hybrid retrieval ablations."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List, Sequence

_TOK = re.compile(r"[a-z0-9]+")
_STOP = frozenset("the a an of and or to in on for with is are was were be by as at from that this it its how what why which does do used use using".split())


def tokenize(text: str) -> List[str]:
    return [t for t in _TOK.findall(text.lower()) if t not in _STOP]


class BM25:
    def __init__(self, docs: Sequence[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(tokenize(d)) for d in docs]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 0.0
        df: Counter = Counter()
        for t in self.tf:
            df.update(t.keys())
        n = len(docs)
        self.idf: Dict[str, float] = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def scores(self, query: str) -> List[float]:
        q = tokenize(query)
        out = []
        for tf, ln in zip(self.tf, self.len):
            s = 0.0
            for w in q:
                f = tf.get(w)
                if f:
                    s += self.idf.get(w, 0.0) * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * ln / (self.avg or 1.0)))
            out.append(s)
        return out


def rrf(score_lists: Sequence[Sequence[float]], k: int = 60) -> List[float]:
    """Reciprocal-rank fusion of several score vectors over the same items."""
    n = len(score_lists[0])
    fused = [0.0] * n
    for scores in score_lists:
        order = sorted(range(n), key=lambda i: -scores[i])
        for rank, i in enumerate(order):
            fused[i] += 1.0 / (k + rank + 1)
    return fused


def structure_guided_rrf(
    chunk_dense: Sequence[float],
    bm25_scores: Sequence[float],
    section_scores: Optional[Sequence[float]] = None,
    alpha_sec: float = 0.003,
    k: int = 60,
) -> List[float]:
    """Reciprocal-rank fusion with STAIR-style structural section guidance."""
    base = rrf([chunk_dense, bm25_scores], k=k)
    if section_scores is not None and alpha_sec > 0:
        return [base[i] + alpha_sec * section_scores[i] for i in range(len(base))]
    return base


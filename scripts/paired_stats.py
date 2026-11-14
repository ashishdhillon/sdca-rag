"""Paired statistics for SDCA per-query retrieval results (pure Python, no extra dependencies).

Usage (from the project root, inside your virtualenv):
    python scripts/paired_stats.py experiments/results_v2/retrieval_results.csv --ref sdca_v2

Reads the per-query CSV written by the experiment runner and prints, for each metric:
  * mean with a 95% bootstrap CI over queries for every strategy
  * paired difference (ref minus other) with a 95% CI, wins/losses/ties and an exact sign-test p-value
    (Holm-adjusted across the comparisons)
  * how many queries would be needed to detect a 0.05 / 0.03 mean difference (80% power, alpha 0.05)
Interpretation: if a paired CI includes 0, the data do not show a difference between those two strategies."""
import argparse
import csv
import math
import random
from collections import defaultdict


def mean(x):
    return sum(x) / len(x)


def sd(x):
    m = mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)) if len(x) > 1 else 0.0


def boot(x, n=5000, seed=0):
    r = random.Random(seed)
    m = sorted(mean([r.choice(x) for _ in x]) for _ in range(n))
    return m[int(0.025 * n)], m[int(0.975 * n)]


def sign_p(d):
    d = [v for v in d if abs(v) > 1e-12]
    n, k = len(d), sum(v > 0 for v in d)
    if not n:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n)


def holm(p):
    items = sorted(p.items(), key=lambda kv: kv[1])
    out, run = {}, 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (len(items) - i) * v))
        out[k] = run
    return out


def needed(s, delta):
    return math.ceil(((1.959964 + 0.841621) * s / delta) ** 2) if s > 0 else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--ref", default="sdca_v2")
    ap.add_argument("--metrics", default="ndcg_at_k,mrr,recall_at_k,precision_at_k,hit_at_k")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    by = defaultdict(dict)
    for r in rows:
        by[r["strategy"]][r["query_id"]] = r
    qs = sorted(set.intersection(*[set(v) for v in by.values()]))
    print(f"{len(qs)} queries, strategies: {', '.join(by)}\n")
    for m in a.metrics.split(","):
        if m not in rows[0]:
            continue
        vec = {s: [float(by[s][q][m]) for q in qs] for s in by}
        print(f"== {m}")
        for s, v in vec.items():
            lo, hi = boot(v)
            print(f"  {s:12s} {mean(v):.3f}  95% CI [{lo:.3f}, {hi:.3f}]")
        pv, res = {}, {}
        for s in by:
            if s == a.ref:
                continue
            d = [x - y for x, y in zip(vec[a.ref], vec[s])]
            lo, hi = boot(d)
            res[s] = (mean(d), lo, hi, sum(v > 1e-12 for v in d), sum(v < -1e-12 for v in d), sd(d))
            pv[s] = sign_p(d)
        adj = holm(pv)
        print(f"  paired: {a.ref} minus other")
        for s, (d, lo, hi, w, l, sdv) in res.items():
            print(f"    vs {s:10s} diff {d:+.3f} [{lo:+.3f}, {hi:+.3f}]  wins/losses {w}/{l}  sign p {pv[s]:.3f}  Holm p {adj[s]:.3f}")
        worst = max((v[5] for v in res.values()), default=0)
        print(f"  queries needed (largest paired SD {worst:.3f}): "
              f"{needed(worst, 0.05)} for a 0.05 difference, {needed(worst, 0.03)} for 0.03\n")


if __name__ == "__main__":
    main()

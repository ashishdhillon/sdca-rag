"""Break retrieval results down by question type / evidence section / evidence count.

  python scripts/qasper_breakdown.py experiments/qasper_dev_b1500/retrieval_results.csv --by ev_section \
      --strategies 'sentence|hybrid,sdca_v2|hybrid,v3_full|hybrid'
Prints mean NDCG and evidence recall per group and strategy with group sizes (n questions).
Small groups (n < 20) are marked '*': do not read anything into them.
"""
import argparse
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("csv"); ap.add_argument("--by", default="ev_section",
                choices=["ev_section", "qtype", "n_evidence"])
ap.add_argument("--strategies", help="comma-separated; default all")
a = ap.parse_args()
df = pd.read_csv(a.csv)
if a.by == "n_evidence":
    df["n_evidence"] = df["n_evidence"].clip(upper=3).map({1: "1", 2: "2", 3: "3+"})
if a.strategies:
    df = df[df["strategy"].isin(a.strategies.split(","))]
for metric, label in (("ndcg_at_k", "NDCG"), ("recall_at_k", "Evidence recall")):
    t = df.pivot_table(index=a.by, columns="strategy", values=metric, aggfunc="mean").round(3)
    n = df.groupby(a.by)["query_id"].nunique() if False else df.groupby(a.by).size() // df["strategy"].nunique()
    t.insert(0, "n", [f"{v}{'*' if v < 20 else ''}" for v in n.reindex(t.index)])
    print(f"\n== {label} by {a.by}\n{t.to_string()}")

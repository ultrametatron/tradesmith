#!/usr/bin/env python
"""
select_candidates.py

Compute a composite score for each symbol and select the top N candidates
based on metric weights defined in metric_weights.json.
"""

import os
import sys
import json
import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────────
STATE_DIR      = "/data/state"
MASTER_FILE    = os.path.join(STATE_DIR, "master_prices.csv")
WEIGHTS_FILE   = os.path.join(STATE_DIR, "metric_weights.json")
OUTPUT_FILE    = os.path.join(STATE_DIR, "top250.csv")
# ────────────────────────────────────────────────────────────────────────────────

def select(top_n: int = 250) -> None:
    """
    Load master_prices.csv and metric_weights.json, compute a weighted
    composite score, and write the top_n rows by score to top250.csv.
    """
    # 1) Load data
    df = pd.read_csv(MASTER_FILE)

    # 2) Load weights
    with open(WEIGHTS_FILE, "r") as f:
        weights = json.load(f)

    # 3) Validate that all weight keys exist in the DataFrame
    missing = [metric for metric in weights if metric not in df.columns]
    if missing:
        raise ValueError(f"Missing metrics in master_prices.csv: {missing}")

    # 4) Compute weighted sum
    df["score"] = sum(df[metric] * weight for metric, weight in weights.items())

    # 5) Select and persist top N
    os.makedirs(STATE_DIR, exist_ok=True)
    df.nlargest(top_n, "score").to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Wrote top {top_n} candidates to {OUTPUT_FILE}")

if __name__ == "__main__":
    # Allow overriding N via command-line arg
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    select(n)

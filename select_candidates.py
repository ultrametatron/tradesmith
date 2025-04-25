"""
Compute composite score and select top candidates.
"""
import pandas as pd, json, sys

def select(top_n=250):
    df = pd.read_csv("state/master_prices.csv")
    weights = json.load(open("state/metric_weights.json"))
    missing = [m for m in weights if m not in df.columns]
    if missing:
        raise ValueError(f"Missing metrics: {missing}")
    # Weighted sum of metrics
    df["score"] = sum(df[m] * w for m, w in weights.items())
    # Export top-n
    df.nlargest(top_n, "score").to_csv("state/top250.csv", index=False)

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    select(n)

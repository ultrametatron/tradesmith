"""
Daily adaptive weighting based on correlation with P&L.
"""
import pandas as pd, json

def update_weights(alpha: float = 0.1):
    df = pd.read_csv("state/signal_performance.csv")
    corrs = df.corr()["pnl"].to_dict()
    w = json.load(open("state/metric_weights.json"))
    for k in w:
        w[k] = max(0, min(1, w[k] + alpha * corrs.get(k, 0)))
    # Renormalize
    total = sum(w.values())
    w = {k: v/total for k, v in w.items()}
    json.dump(w, open("state/metric_weights.json","w"), indent=2)

"""
Apply model-provided adjustments to holdings and log commissions.
"""
import pandas as pd, datetime

def apply(adjustments: list):
    df = pd.read_csv("state/holdings.csv")
    logs = []
    for adj in adjustments:
        mask = df.Symbol == adj["symbol"]
        price = df.loc[mask, "Price"].iloc[0]
        df.loc[mask, "Shares"] = adj["shares"]
        df.loc[mask, "Weight"] = adj["new_weight"]
        logs.append({
            "Symbol":      adj["symbol"],
            "Cost":        adj["shares"] * price,
            "Commission":  adj["est_commission"],
            "Timestamp":   datetime.datetime.utcnow()
        })
    df.to_csv("state/holdings.csv", index=False)
    if logs:
        pd.DataFrame(logs).to_csv("state/commissions_log.csv", mode="a", header=False, index=False)

"""
Log equity curve and compute daily/weekly KPIs.
"""
import pandas as pd, numpy as np, datetime

def log(df):
    """Append current portfolio value to equity log."""
    total = df.Value.sum()
    pd.DataFrame([{"date": datetime.datetime.utcnow(), "value": total}]) \
      .to_csv("state/equity_log.csv", mode="a", header=False, index=False)

def metrics() -> dict:
    """Compute return, Sharpe, Sortino, max drawdown."""
    eq = pd.read_csv("state/equity_log.csv", names=["date","value"], parse_dates=["date"])
    r = eq.value.pct_change().dropna()
    sharpe  = np.sqrt(252) * r.mean()/r.std() if r.std() else 0
    sortino = np.sqrt(252) * r.mean()/r[r<0].std() if any(r<0) else 0
    mdd     = (eq.value.cummax() - eq.value).max()/eq.value.cummax().max()
    return {"return": r.add(1).prod()-1, "sharpe": sharpe, "sortino": sortino, "max_dd": mdd}

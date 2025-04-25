# update_top250_live.py

import os
import time
import datetime
import requests
import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────────
FMP_KEY  = os.getenv("FMP_API_KEY")
if not FMP_KEY:
    raise RuntimeError("FMP_API_KEY environment variable is not set")

BASE_URL = "https://financialmodelingprep.com/api/v3"
STATE_DIR = "state"
TOP250_FILE = os.path.join(STATE_DIR, "top250.csv")
MASTER_FILE = os.path.join(STATE_DIR, "master_prices.csv")
LIVE_FILE   = os.path.join(STATE_DIR, "top250_live.csv")
# ─────────────────────────────────────────────────────────────────────────────────

def fetch_prices(symbols: list[str]) -> pd.DataFrame:
    """
    Batch real-time quotes via FMP /quote endpoint.
    Returns a DataFrame with columns: Symbol, Price, ChangePct, Volume, Timestamp.
    """
    if not symbols:
        return pd.DataFrame([], columns=["Symbol","Price","ChangePct","Volume","Timestamp"])
    url = f"{BASE_URL}/quote/{','.join(symbols)}"
    resp = requests.get(url, params={"apikey": FMP_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    now = datetime.datetime.utcnow()
    rows = []
    for d in data:
        price = d.get("price", 0.0)
        prev  = d.get("previousClose") or price
        rows.append({
            "Symbol":    d.get("symbol"),
            "Price":     price,
            "ChangePct": (price - prev) / prev if prev else 0.0,
            "Volume":    d.get("volume", 0),
            "Timestamp": now
        })
    return pd.DataFrame(rows)

def update_top250_live():
    # 1) Load precomputed metrics and top250 list
    df_master = pd.read_csv(MASTER_FILE)
    df_top250 = pd.read_csv(TOP250_FILE)
    symbols   = df_top250["Symbol"].astype(str).tolist()

    # 2) Fetch fresh prices for top250
    df_prices = fetch_prices(symbols)

    # 3) Merge live prices onto precomputed metrics
    #    Keep only symbols in the top250 list
    df_live = (
        df_master
        .merge(df_prices, on="Symbol", how="inner", suffixes=("_old",""))
    )

    # 4) Persist live snapshot
    os.makedirs(STATE_DIR, exist_ok=True)
    df_live.to_csv(LIVE_FILE, index=False)
    print(f"[update_top250_live] Wrote {len(df_live)} rows to {LIVE_FILE}")

if __name__ == "__main__":
    update_top250_live()

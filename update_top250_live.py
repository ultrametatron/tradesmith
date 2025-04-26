#!/usr/bin/env python
"""
update_top250_live.py

1. Read /data/state/top250.csv (your candidate list).
2. Batch‐fetch real‐time quotes from FMP.
3. Merge onto /data/state/master_prices.csv.
4. Write /data/state/top250_live.csv.
"""

import os
import datetime
import requests
import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────────
FMP_KEY     = os.getenv("FMP_API_KEY")
if not FMP_KEY:
    raise RuntimeError("FMP_API_KEY environment variable is required")

BASE_URL    = "https://financialmodelingprep.com/api/v3"
STATE_DIR   = "/data/state"
MASTER_FILE = os.path.join(STATE_DIR, "master_prices.csv")
TOP250_FILE = os.path.join(STATE_DIR, "top250.csv")
LIVE_FILE   = os.path.join(STATE_DIR, "top250_live.csv")
# ────────────────────────────────────────────────────────────────────────────────

def fetch_prices(symbols: list[str]) -> pd.DataFrame:
    """Fetch current quote for a list of symbols."""
    if not symbols:
        return pd.DataFrame(columns=["Symbol","Price","ChangePct","Volume","Timestamp"])

    url = f"{BASE_URL}/quote/{','.join(symbols)}"
    resp = requests.get(url, params={"apikey": FMP_KEY}, timeout=10)
    resp.raise_for_status()
    now = datetime.datetime.utcnow()

    records = []
    for d in resp.json():
        prev = d.get("previousClose") or d.get("price", 0)
        price = d.get("price", 0.0)
        records.append({
            "Symbol":    d["symbol"],
            "Price":     price,
            "ChangePct": (price - prev)/prev if prev else 0.0,
            "Volume":    d.get("volume", 0),
            "Timestamp": now
        })

    return pd.DataFrame(records)

def update_top250_live():
    """Load master + top250, fetch live quotes, merge & persist."""
    # Ensure the state directory exists
    os.makedirs(STATE_DIR, exist_ok=True)

    # Load static metrics and candidate list
    df_master = pd.read_csv(MASTER_FILE)
    df_top    = pd.read_csv(TOP250_FILE)
    symbols   = df_top["Symbol"].astype(str).tolist()

    # Get live quotes
    df_prices = fetch_prices(symbols)

    # Merge on Symbol
    df_live = df_master.merge(df_prices, on="Symbol", how="inner")

    # Persist live snapshot
    df_live.to_csv(LIVE_FILE, index=False)
    print(f"✅ top250_live.csv: Wrote {len(df_live)} rows to {LIVE_FILE}")

if __name__ == "__main__":
    update_top250_live()

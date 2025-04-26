#!/usr/bin/env python
"""
update_master_prices.py

Single‐pass over the universe in 500‐symbol batches:

 • Batch /quote and /profile calls
 • Per‐symbol /historical-price-full to compute MA50, MA200, YTDChange
 • Write /data/state/master_prices.csv with all metrics
"""

import os
import time
import datetime
import requests
import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────────
FMP_KEY    = os.getenv("FMP_API_KEY")
if not FMP_KEY:
    raise RuntimeError("FMP_API_KEY environment variable is required")

BASE_URL   = "https://financialmodelingprep.com/api/v3"
BATCH_SIZE = 500
HIST_DAYS  = 365

STATE_DIR      = "/data/state"
TICKERS_FILE   = os.path.join(STATE_DIR, "master_tickers.csv")
MASTER_PRICES  = os.path.join(STATE_DIR, "master_prices.csv")
# ────────────────────────────────────────────────────────────────────────────────

def fetch_prices(batch: list[str]) -> list[dict]:
    """Fetch real‐time quotes for one batch of symbols."""
    url = f"{BASE_URL}/quote/{','.join(batch)}"
    resp = requests.get(url, params={"apikey": FMP_KEY})
    resp.raise_for_status()
    now = datetime.datetime.utcnow()
    data = resp.json()
    rows = []
    for d in data:
        prev = d.get("previousClose") or d.get("price", 0)
        rows.append({
            "Symbol":    d["symbol"],
            "Price":     d.get("price", 0.0),
            "ChangePct": (d.get("price", 0.0) - prev) / prev if prev else 0.0,
            "Volume":    d.get("volume", 0),
            "Timestamp": now
        })
    return rows

def fetch_profiles(batch: list[str]) -> list[dict]:
    """Fetch static profile data (sector, beta, etc.) for one batch."""
    url = f"{BASE_URL}/profile/{','.join(batch)}"
    resp = requests.get(url, params={"apikey": FMP_KEY})
    resp.raise_for_status()
    data = resp.json()
    rows = []
    for d in data:
        rows.append({
            "Symbol":     d["symbol"],
            "Sector":     d.get("sector"),
            "Industry":   d.get("industry"),
            "Country":    d.get("country"),
            "MarketCap":  d.get("mktCap", 0),
            "Beta":       d.get("beta", 0.0),
            "PERatio":    d.get("priceEarningsRatio"),
            "PBRatio":    d.get("priceToBookRatio"),
            "LastDiv":    d.get("lastDiv", 0.0),
        })
    return rows

def fetch_history(sym: str) -> list[dict]:
    """Fetch up to HIST_DAYS of historical closes for a symbol."""
    url = f"{BASE_URL}/historical-price-full/{sym}"
    resp = requests.get(url, params={"apikey": FMP_KEY, "timeseries": HIST_DAYS})
    resp.raise_for_status()
    return resp.json().get("historical", [])

def compute_metrics_for_batch(df: pd.DataFrame) -> None:
    """Add MA50, MA200, YTDChange, DividendYield columns to df in place."""
    year = str(datetime.datetime.utcnow().year)
    ma50, ma200, ytd = [], [], []

    for sym, price, last_div in zip(df.Symbol, df.Price, df.LastDiv):
        hist = fetch_history(sym)
        closes = [h["close"] for h in hist]
        ma50.append(sum(closes[:50]) / 50 if len(closes) >= 50 else None)
        ma200.append(sum(closes[:200]) / 200 if len(closes) >= 200 else None)

        # YTD: find the last close in this year
        yc = [h["close"] for h in hist if h["date"].startswith(year)]
        ytd.append((closes[0] / yc[-1] - 1) if yc and yc[-1] else None)

    df["MA50"] = ma50
    df["MA200"] = ma200
    df["YTDChange"] = ytd
    df["DividendYield"] = df["LastDiv"].fillna(0) / df["Price"].replace({0: None})

def update_master():
    """Orchestrate the full universe refresh and write to disk."""
    # Ensure data directory exists
    os.makedirs(STATE_DIR, exist_ok=True)

    # Load your master ticker list
    tickers = pd.read_csv(TICKERS_FILE)["Symbol"].tolist()

    all_batches = []
    for i in range(0, len(tickers), BATCH_SIZE):
        batch   = tickers[i : i + BATCH_SIZE]
        prices  = fetch_prices(batch)
        profs   = fetch_profiles(batch)
        df_batch= pd.DataFrame(prices).merge(pd.DataFrame(profs), on="Symbol", how="left")

        compute_metrics_for_batch(df_batch)
        all_batches.append(df_batch)

        time.sleep(0.2)  # to stay under rate limits

    # Combine and persist
    df_all = pd.concat(all_batches, ignore_index=True)
    df_all.to_csv(MASTER_PRICES, index=False)
    print(f"✅ master_prices.csv: {len(df_all)} rows with all metrics")

if __name__ == "__main__":
    update_master()

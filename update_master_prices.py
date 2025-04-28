"""
update_master_prices.py

Fetches fundamentals in batches and writes master_prices.csv
into the shared /data/state folder for intraday use.
"""

import os
import time
import datetime
import requests
import pandas as pd

# ── Config ───────────────────────────────────────────────────────────────────────
STATE_DIR          = "/data/state"
TICKERS_FILE       = os.path.join(STATE_DIR, "master_tickers.csv")
MASTER_PRICES_FILE = os.path.join(STATE_DIR, "master_prices.csv")

FMP_KEY   = os.getenv("FMP_API_KEY") or RuntimeError("FMP_API_KEY required")
BASE_URL  = "https://financialmodelingprep.com/api/v3"
BATCH_SIZE = 500
HIST_DAYS  = 365
# ────────────────────────────────────────────────────────────────────────────────

def fetch_prices(batch):
    url = f"{BASE_URL}/quote/{','.join(batch)}"
    resp = requests.get(url, params={"apikey": FMP_KEY})
    resp.raise_for_status()
    data = resp.json()
    now = datetime.datetime.utcnow()
    return [
        {
            "Symbol": d["symbol"],
            "Price": d.get("price", 0),
            "ChangePct": ((d.get("price", 0) - d.get("previousClose", 0))
                          / (d.get("previousClose") or 1)),
            "Volume": d.get("volume", 0),
            "Timestamp": now
        }
        for d in data
    ]

def fetch_profiles(batch):
    url = f"{BASE_URL}/profile/{','.join(batch)}"
    resp = requests.get(url, params={"apikey": FMP_KEY})
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "Symbol": d["symbol"],
            "Sector": d.get("sector"),
            "Industry": d.get("industry"),
            "Country": d.get("country"),
            "MarketCap": d.get("mktCap", 0),
            "Beta": d.get("beta", 0),
            "PERatio": d.get("priceEarningsRatio"),
            "PBRatio": d.get("priceToBookRatio"),
            "LastDiv": d.get("lastDiv", 0)
        }
        for d in data
    ]

def fetch_history(symbol):
    url = f"{BASE_URL}/historical-price-full/{symbol}"
    resp = requests.get(
        url,
        params={"apikey": FMP_KEY, "timeseries": HIST_DAYS}
    )
    resp.raise_for_status()
    return resp.json().get("historical", [])

def compute_metrics_for_batch(df):
    year = str(datetime.datetime.utcnow().year)
    ma50, ma200, ytd = [], [], []
    for sym, price, last_div in zip(df.Symbol, df.Price, df.LastDiv):
        hist = fetch_history(sym)
        closes = [h["close"] for h in hist]
        ma50.append(sum(closes[:50]) / 50 if len(closes) >= 50 else None)
        ma200.append(sum(closes[:200]) / 200 if len(closes) >= 200 else None)
        # Year-to-date change
        y0 = next((h["close"] for h in hist if h["date"].startswith(year)), None)
        ytd.append((closes[0]/y0 - 1) if y0 and closes else None)
    df["MA50"]         = ma50
    df["MA200"]        = ma200
    df["YTDChange"]    = ytd
    df["DivYield"]     = df["LastDiv"].fillna(0) / df["Price"].replace({0: None})

def update_master():
    # 1) ensure state folder exists
    os.makedirs(STATE_DIR, exist_ok=True)

    # 2) load universe
    tickers = pd.read_csv(TICKERS_FILE)["Symbol"].tolist()
    all_batches = []

    # 3) process in chunks
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i : i + BATCH_SIZE]
        prices = fetch_prices(batch)
        profs  = fetch_profiles(batch)
        dfb = pd.DataFrame(prices).merge(
            pd.DataFrame(profs), on="Symbol", how="left"
        )
        compute_metrics_for_batch(dfb)
        all_batches.append(dfb)
        time.sleep(0.2)  # keep under rate limits

    # 4) combine & persist
    df_master = pd.concat(all_batches, ignore_index=True)
    df_master.to_csv(MASTER_PRICES_FILE, index=False)
    print(f"Written {len(df_master)} rows to {MASTER_PRICES_FILE}")

if __name__ == "__main__":
    update_master()
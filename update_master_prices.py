"""
update_master_prices.py

Fetch real-time quotes & company profiles in batches from Financial Modeling Prep (FMP),
then compute technical metrics (MA50, MA200, YTD change) via yfinance history,
and DividendYield from FMP profile data. Writes out `state/master_prices.csv`.
"""

import os
import time
import datetime
import requests
import pandas as pd
import yfinance as yf

# ── Configuration ────────────────────────────────────────────────────────────────
FMP_KEY = os.getenv("FMP_API_KEY")
if not FMP_KEY:
    raise RuntimeError("FMP_API_KEY environment variable is not set")

BASE_URL = "https://financialmodelingprep.com/api/v3"
BATCH_SIZE = 500             # number of symbols per FMP batch call
HISTORY_PERIOD = "365d"      # how much history to pull for MA/YTD
HISTORY_INTERVAL = "1d"      # daily bars for moving averages
# ─────────────────────────────────────────────────────────────────────────────────

def fetch_prices(symbols):
    """
    Batch real-time quotes via FMP /quote endpoint.
    Returns list of dicts: Symbol, Price, ChangePct, Volume, Timestamp.
    """
    if not symbols:
        return []
    url = f"{BASE_URL}/quote/{','.join(symbols)}"
    resp = requests.get(url, params={"apikey": FMP_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    rows = []
    now = datetime.datetime.utcnow()
    for d in data:
        price = d.get("price")
        prev = d.get("previousClose") or price
        rows.append({
            "Symbol":    d.get("symbol"),
            "Price":     price,
            "ChangePct": (price - prev) / prev if prev else 0.0,
            "Volume":    d.get("volume"),
            "Timestamp": now,
        })
    return rows

def fetch_profiles(symbols):
    """
    Batch company profiles via FMP /profile endpoint.
    Returns list of dicts: Symbol, Sector, Industry, Country, MarketCap, Beta, PERatio, PBRatio, LastDiv.
    """
    if not symbols:
        return []
    url = f"{BASE_URL}/profile/{','.join(symbols)}"
    resp = requests.get(url, params={"apikey": FMP_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    rows = []
    for d in data:
        rows.append({
            "Symbol":       d.get("symbol"),
            "Sector":       d.get("sector"),
            "Industry":     d.get("industry"),
            "Country":      d.get("country"),
            "MarketCap":    d.get("mktCap"),
            "Beta":         d.get("beta"),
            "PERatio":      d.get("priceEarningsRatio"),
            "PBRatio":      d.get("priceToBookRatio"),
            "LastDiv":      d.get("lastDiv", 0.0),
        })
    return rows

def compute_technical_metrics(df):
    """
    For each symbol in df, fetch HISTORY via yfinance and compute:
      - MA50: 50-day moving average of Close
      - MA200: 200-day moving average of Close
      - YTDChange: (latest close / first close of current year) - 1
      - DividendYield: LastDiv / Price
    Operates in-place on df.
    """
    symbols = df["Symbol"].tolist()
    # fetch history for all at once
    yf_data = yf.Tickers(" ".join(symbols))
    ma50_list, ma200_list, ytd_list = [], [], []
    today = datetime.datetime.utcnow().date()
    year_start = datetime.date(today.year, 1, 1)

    for sym in symbols:
        try:
            hist = yf_data.tickers[sym].history(period=HISTORY_PERIOD, interval=HISTORY_INTERVAL)
            closes = hist["Close"].dropna()
            ma50 = closes.rolling(50).mean().iloc[-1] if len(closes) >= 50 else None
            ma200 = closes.rolling(200).mean().iloc[-1] if len(closes) >= 200 else None

            # YTD: find first close on or after Jan 1
            ytd_start = closes.loc[closes.index.date >= year_start]
            ytd0 = ytd_start.iloc[0] if len(ytd_start) > 0 else closes.iloc[0]
            ytd_change = (closes.iloc[-1] / ytd0) - 1 if ytd0 else 0.0
        except Exception:
            ma50, ma200, ytd_change = None, None, None

        ma50_list.append(ma50)
        ma200_list.append(ma200)
        ytd_list.append(ytd_change)

    df["MA50"] = ma50_list
    df["MA200"] = ma200_list
    df["YTDChange"] = ytd_list
    # Dividend yield = last dividend amount / current price
    df["DividendYield"] = df["LastDiv"].fillna(0.0) / df["Price"].replace({0: None})

def update_master():
    # 1. load universe
    tickers = pd.read_csv("state/master_tickers.csv").Symbol.tolist()
    price_rows, profile_rows = [], []

    # 2. fetch in batches
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i : i + BATCH_SIZE]
        price_rows.extend(fetch_prices(batch))
        profile_rows.extend(fetch_profiles(batch))
        time.sleep(0.2)  # throttle under rate limit

    # 3. build DataFrames and merge on Symbol
    df_price   = pd.DataFrame(price_rows)
    df_profile = pd.DataFrame(profile_rows)
    df_master  = df_price.merge(df_profile, on="Symbol", how="left")

    # 4. compute technical metrics
    compute_technical_metrics(df_master)

    # 5. save to CSV for downstream use
    os.makedirs("state", exist_ok=True)
    df_master.to_csv("state/master_prices.csv", index=False)
    print(f"Updated master_prices.csv with {len(df_master)} rows.")

if __name__ == "__main__":
    update_master()

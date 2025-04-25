"""
update_master_prices.py

Fetch real-time quotes and categorical/fundamental data in batches
from Financial Modeling Prep (FMP). Writes `state/master_prices.csv`.
"""

import os
import time
import pandas as pd
import requests
import datetime

# FMP configuration
FMP_KEY = os.getenv("FMP_API_KEY")
BASE    = "https://financialmodelingprep.com/api/v3"
BATCH   = 500   # keep at 500 symbols per request for efficiency

def fetch_prices(symbols):
    """
    Batch real-time quotes via FMP /quote endpoint.
    Returns list of dicts with keys: Symbol, Price, ChangePct, Volume, Timestamp.
    """
    if not symbols:
        return []
    sym_list = ",".join(symbols)
    url = f"{BASE}/quote/{sym_list}"
    resp = requests.get(url, params={"apikey": FMP_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()  # list of {symbol, price, change, ...}
    rows = []
    for d in data:
        rows.append({
            "Symbol":     d.get("symbol"),
            "Price":      d.get("price"),
            "ChangePct":  d.get("change") / d.get("previousClose") if d.get("previousClose") else 0,
            "Volume":     d.get("volume"),
            "Timestamp":  datetime.datetime.utcnow()
        })
    return rows

def fetch_profiles(symbols):
    """
    Batch company profiles via FMP /profile endpoint.
    Returns list of dicts with keys: Symbol, Sector, Industry, Country, MarketCap, Beta, PERatio, PBRatio.
    """
    if not symbols:
        return []
    sym_list = ",".join(symbols)
    url = f"{BASE}/profile/{sym_list}"
    resp = requests.get(url, params={"apikey": FMP_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()  # list of profile dicts
    rows = []
    for d in data:
        rows.append({
            "Symbol":     d.get("symbol"),
            "Sector":     d.get("sector"),
            "Industry":   d.get("industry"),
            "Country":    d.get("country"),
            "MarketCap":  d.get("mktCap"),
            "Beta":       d.get("beta"),
            "PERatio":    d.get("priceEarningsRatio"),
            "PBRatio":    d.get("priceToBookRatio")
        })
    return rows

def update_master():
    """
    1. Read universe from state/master_tickers.csv
    2. For each batch of BATCH symbols:
       - fetch_prices
       - fetch_profiles
    3. Merge price & profile tables on Symbol
    4. Save to state/master_prices.csv
    """
    tickers = pd.read_csv("state/master_tickers.csv").Symbol.tolist()
    price_rows, profile_rows = [], []

    # Fetch price data in batches
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i : i + BATCH]
        price_rows.extend(fetch_prices(batch))
        time.sleep(0.2)  # stay well under rate limit

    # Fetch profile data in same batches
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i : i + BATCH]
        profile_rows.extend(fetch_profiles(batch))
        time.sleep(0.2)

    # Build DataFrames and merge
    df_price   = pd.DataFrame(price_rows)
    df_profile = pd.DataFrame(profile_rows)
    df_master  = df_price.merge(df_profile, on="Symbol", how="left")

    # Optional: compute any additional metrics here (MA50/MA200/YTD etc.)

    # Persist for downstream steps
    df_master.to_csv("state/master_prices.csv", index=False)
    print(f"Updated master_prices.csv with {len(df_master)} rows.")

if __name__ == "__main__":
    update_master()

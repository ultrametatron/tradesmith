#!/usr/bin/env python3
"""
Phase 2: Ingest full symbol universe, quotes + fundamentals
into BigQuery raw_market.symbols, quotes_intraday, fundamentals_daily.
"""

import os
import time
import requests
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest

# CONFIGURATION
PROJECT_ID    = os.getenv("GCP_PROJECT", "tradesmith-458506")
BQ_DATASET    = "raw_market"
FMP_API_KEY   = os.environ["FMP_API_KEY"]
FMP_BASE      = "https://financialmodelingprep.com/api/v3"

# CLIENT
bq = bigquery.Client(project=PROJECT_ID)

def create_symbol_table():
    """Stage 1: Pull master symbol list and write to BQ."""
    url = f"{FMP_BASE}/stock/list?apikey={FMP_API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    symbols = resp.json()  # list of {symbol, name, exchangeShortName, ...}

    rows = [
        {
            "symbol": s["symbol"],
            "name":   s.get("name", ""),
            "exchange": s.get("exchangeShortName", "")
        }
        for s in symbols
    ]

    table_id = f"{PROJECT_ID}.{BQ_DATASET}.symbols"
    print(f"Inserting {len(rows)} symbols into {table_id}…")
    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        print("Symbol insert errors:", errors)
    else:
        print("Symbols loaded successfully.")

def ingest_quotes(tickers, limit=1):
    """Stage 2: For each ticker, fetch latest quote and write to BQ."""
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.quotes_intraday"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/quote/{t}?apikey={FMP_API_KEY}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        if not data: continue
        q = data[0]
        rows.append({
            "ticker": t,
            "ts":      q["timestamp"],     # Unix seconds OK for TIMESTAMP
            "price":   q["price"],
            "volume":  q["volume"]
        })
        # avoid rate limits
        time.sleep(0.1)

    print(f"Inserting {len(rows)} quotes into {table_id}…")
    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        print("Quote insert errors:", errors)
    else:
        print("Quotes loaded successfully.")

def ingest_fundamentals(tickers):
    """Stage 3: For each ticker, fetch company profile and write JSON blob."""
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.fundamentals_daily"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/profile/{t}?apikey={FMP_API_KEY}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        if not data: continue
        profile = data[0]
        rows.append({
            "ticker":       t,
            "as_of_date":   profile.get("priceDate"),  
            "json_payload": profile
        })
        time.sleep(0.1)

    print(f"Inserting {len(rows)} fundamentals into {table_id}…")
    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        print("Fundamentals insert errors:", errors)
    else:
        print("Fundamentals loaded successfully.")

def main():
    # 1) Symbols
    create_symbol_table()

    # For demo/testing, limit to first 50 tickers
    query = f"SELECT symbol FROM `{PROJECT_ID}.{BQ_DATASET}.symbols` LIMIT 50"
    tickers = [row.symbol for row in bq.query(query)]
    print("Ingesting for tickers:", tickers[:5], "…")

    # 2) Quotes + Fundamentals
    ingest_quotes(tickers)
    ingest_fundamentals(tickers)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Phase 2 (filtered): Ingest Wilshire 5000 symbols, plus quotes & fundamentals for first 250 tickers.
"""

import os
import time
import csv
import requests
from google.cloud import bigquery

# ─── CONFIGURATION ───────────────────────────────────────────────────────────────
PROJECT_ID  = os.getenv("GCP_PROJECT", "tradesmith-458506")
BQ_DATASET  = "raw_market"
FMP_API_KEY = os.environ["FMP_API_KEY"]
FMP_BASE    = "https://financialmodelingprep.com/api/v3"
CSV_FILE    = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
MAX_TICKERS = 250
# ────────────────────────────────────────────────────────────────────────────────

# Initialize BigQuery client
bq = bigquery.Client(project=PROJECT_ID)

def load_wilshire_symbols(csv_path):
    """Read Wilshire 5000 symbols from CSV. Expects header row with 'symbol' column."""
    symbols = []
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        try:
            idx = header.index("symbol")
        except ValueError:
            idx = 0
        for row in reader:
            sym = row[idx].strip().upper()
            if sym:
                symbols.append(sym)
    return symbols

def write_symbols(symbols):
    """Stream the list of symbols into raw_market.symbols."""
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.symbols"
    rows = [{"symbol": s, "name": "", "exchange": ""} for s in symbols]
    print(f"Inserting {len(rows)} Wilshire symbols into {table_id}…")
    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        print("⚠️ Symbol insert errors:", errors)
    else:
        print("✅ Symbols loaded.")

def ingest_quotes(tickers):
    """Fetch latest quote for each ticker and write to quotes_intraday."""
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.quotes_intraday"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/quote/{t}?apikey={FMP_API_KEY}"
        resp = requests.get(url); resp.raise_for_status()
        data = resp.json()
        if data:
            q = data[0]
            rows.append({
                "ticker": t,
                "ts":      q["timestamp"],   # BigQuery will parse UNIX seconds
                "price":   q["price"],
                "volume":  q["volume"]
            })
        time.sleep(0.1)  # throttle
    print(f"Inserting {len(rows)} quotes into {table_id}…")
    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        print("⚠️ Quote insert errors:", errors)
    else:
        print("✅ Quotes loaded.")

def ingest_fundamentals(tickers):
    """Fetch company profile per ticker and write raw JSON into fundamentals_daily."""
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.fundamentals_daily"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/profile/{t}?apikey={FMP_API_KEY}"
        resp = requests.get(url); resp.raise_for_status()
        data = resp.json()
        if data:
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
        print("⚠️ Fundamentals insert errors:", errors)
    else:
        print("✅ Fundamentals loaded.")

def main():
    # 1) Load and write Wilshire symbols
    symbols = load_wilshire_symbols(CSV_FILE)
    write_symbols(symbols)

    # 2) Take first MAX_TICKERS for detailed ingestion
    tickers = symbols[:MAX_TICKERS]
    print(f"Processing quotes & fundamentals for first {len(tickers)} tickers…")

    # 3) Ingest quotes and fundamentals
    ingest_quotes(tickers)
    ingest_fundamentals(tickers)

if __name__ == "__main__":
    main()

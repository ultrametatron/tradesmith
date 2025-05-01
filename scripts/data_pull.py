#!/usr/bin/env python3
"""
Phase 2: Ingest Wilshire 5000 symbols + quotes & fundamentals,
explicitly loading service-account credentials from sa.json,
quoting first 250 tickers, and batching fundamentals for all symbols
in large chunks to minimize requests.
"""

import os
import time
import csv
import json
import requests
from google.cloud import bigquery, secretmanager_v1
from google.oauth2 import service_account

# ─── CONFIG ─────────────────────────────────────────────────────────────
PROJECT               = os.getenv("GCP_PROJECT", "tradesmith-458506")
DATASET               = "raw_market"
CSV_FILE              = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
MAX_QUOTE_TICKERS     = 3500        # number of tickers to fetch intraday for
FUNDAMENTAL_BATCH     = 1000       # chunk size for bulk fundamentals calls
FMP_BASE              = "https://financialmodelingprep.com/api/v3"
SA_JSON_PATH          = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
FMP_SECRET_RESOURCE   = f"projects/{PROJECT}/secrets/FMP_API_KEY/versions/latest"
# ────────────────────────────────────────────────────────────────────────

def load_credentials():
    """Load service-account JSON from sa.json and return Credentials."""
    if not os.path.exists(SA_JSON_PATH):
        raise FileNotFoundError(f"{SA_JSON_PATH} not found.")
    return service_account.Credentials.from_service_account_file(SA_JSON_PATH)

def get_fmp_key(creds):
    """Fetch the FMP API key from Secret Manager."""
    sm = secretmanager_v1.SecretManagerServiceClient(credentials=creds)
    resp = sm.access_secret_version(name=FMP_SECRET_RESOURCE)
    return resp.payload.data.decode("utf-8").strip()

def load_symbols():
    """Read tickers from CSV; expects a 'symbol' column."""
    symbols = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = header.index("symbol") if "symbol" in header else 0
        for row in reader:
            s = row[idx].strip().upper()
            if s:
                symbols.append(s)
    return symbols

def write_symbols(bq, symbols):
    """Stream the full CSV list into raw_market.symbols."""
    table = f"{PROJECT}.{DATASET}.symbols"
    rows = [{"symbol": s, "name": "", "exchange": ""} for s in symbols]
    print(f"Inserting {len(rows)} symbols into {table}…")
    errs = bq.insert_rows_json(table, rows)
    print("⚠️ Symbol insert errors:", errs) if errs else print("✅ Symbols loaded")

def ingest_quotes(bq, tickers, fmp_key):
    """Fetch latest quote per ticker and write into quotes_intraday."""
    table = f"{PROJECT}.{DATASET}.quotes_intraday"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/quote/{t}?apikey={fmp_key}"
        resp = requests.get(url); resp.raise_for_status()
        data = resp.json()
        if data:
            q = data[0]
            rows.append({
                "ticker": t,
                "ts":      q["timestamp"],
                "price":   q["price"],
                "volume":  q["volume"]
            })
        time.sleep(0.1)  # throttle to avoid rate limits
    print(f"Inserting {len(rows)} quotes into {table}…")
    errs = bq.insert_rows_json(table, rows)
    print("⚠️ Quote insert errors:", errs) if errs else print("✅ Quotes loaded")

def ingest_fundamentals(bq, symbols, fmp_key):
    """
    Fetch profiles in large batches and write them into fundamentals_daily.
    We chunk the entire symbols list into FUNDAMENTAL_BATCH-size requests.
    """
    table = f"{PROJECT}.{DATASET}.fundamentals_daily"
    rows = []
    for start in range(0, len(symbols), FUNDAMENTAL_BATCH):
        batch = symbols[start:start+FUNDAMENTAL_BATCH]
        tickers_str = ",".join(batch)
        url = f"{FMP_BASE}/profile/{tickers_str}?apikey={fmp_key}"

        # exponential backoff for 429
        for attempt in range(5):
            resp = requests.get(url)
            if resp.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"⚠️ 429 on fundamentals batch {start//FUNDAMENTAL_BATCH+1}, sleeping {wait}s…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        else:
            raise RuntimeError(f"Failed to fetch fundamentals for batch starting at {start}")

        for p in data:
            # store payload as JSON string for BigQuery JSON column
            rows.append({
                "ticker":       p.get("symbol"),
                "as_of_date":   p.get("priceDate"),
                "json_payload": json.dumps(p)
            })

        time.sleep(1)  # small pause between batches

    print(f"Inserting {len(rows)} fundamentals into {table}…")
    errs = bq.insert_rows_json(table, rows)
    print("⚠️ Fundamentals insert errors:", errs) if errs else print("✅ Fundamentals loaded")

def main():
    creds     = load_credentials()
    bq_client = bigquery.Client(project=PROJECT, credentials=creds)
    fmp_key   = get_fmp_key(creds)

    symbols = load_symbols()
    write_symbols(bq_client, symbols)

    # intraday quotes only for top MAX_QUOTE_TICKERS
    quote_tickers = symbols[:MAX_QUOTE_TICKERS]
    print(f"Processing quotes for {len(quote_tickers)} tickers…")
    ingest_quotes(bq_client, quote_tickers, fmp_key)

    # fundamentals for ALL symbols, batched
    print(f"Processing fundamentals for {len(symbols)} tickers in batches of {FUNDAMENTAL_BATCH}…")
    ingest_fundamentals(bq_client, symbols, fmp_key)

if __name__ == "__main__":
    main()

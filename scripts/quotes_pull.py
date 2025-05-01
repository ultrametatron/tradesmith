#!/usr/bin/env python3
"""
Intraday Quotes Pull

Fetches the latest quotes for the first MAX_QUOTE_TICKERS tickers.
"""

import os
import time
import csv
import requests
from google.cloud import bigquery, secretmanager_v1
from google.oauth2 import service_account

# ─── CONFIG ─────────────────────────────────────────────────────────────
PROJECT            = os.getenv("GCP_PROJECT", "tradesmith-458506")
DATASET            = "raw_market"
CSV_FILE           = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
MAX_QUOTE_TICKERS  = 250          # tune as needed
FMP_BASE           = "https://financialmodelingprep.com/api/v3"
SA_JSON            = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
FMP_SECRET         = f"projects/{PROJECT}/secrets/FMP_API_KEY/versions/latest"
# ────────────────────────────────────────────────────────────────────────

def load_credentials():
    """Load service-account JSON from sa.json."""
    if not os.path.exists(SA_JSON):
        raise FileNotFoundError(f"{SA_JSON} not found.")
    return service_account.Credentials.from_service_account_file(SA_JSON)

def get_fmp_key(creds):
    """Fetch the FMP API key from Secret Manager."""
    sm = secretmanager_v1.SecretManagerServiceClient(credentials=creds)
    resp = sm.access_secret_version(name=FMP_SECRET)
    return resp.payload.data.decode("utf-8").strip()

def load_symbols():
    """Read all Wilshire tickers from CSV (header 'symbol')."""
    syms = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = header.index("symbol") if "symbol" in header else 0
        for row in reader:
            s = row[idx].strip().upper()
            if s:
                syms.append(s)
    return syms

def ingest_quotes(bq, tickers, fmp_key):
    """Fetch and load intraday quotes for the given tickers."""
    table = f"{PROJECT}.{DATASET}.quotes_intraday"
    rows = []
    for t in tickers:
        resp = requests.get(f"{FMP_BASE}/quote/{t}?apikey={fmp_key}")
        resp.raise_for_status()
        data = resp.json()
        if data:
            q = data[0]
            rows.append({
                "ticker": t,
                "ts":      q["timestamp"],
                "price":   q["price"],
                "volume":  q["volume"]
            })
        time.sleep(0.05)  # throttle lightly

    print(f"Inserting {len(rows)} quotes into {table}…")
    errors = bq.insert_rows_json(table, rows)
    if errors:
        print("⚠️ Quote insert errors:", errors)
    else:
        print("✅ Quotes loaded")

def main():
    creds    = load_credentials()
    bq       = bigquery.Client(project=PROJECT, credentials=creds)
    fmp_key  = get_fmp_key(creds)
    symbols  = load_symbols()[:MAX_QUOTE_TICKERS]

    print(f"Processing quotes for {len(symbols)} tickers…")
    ingest_quotes(bq, symbols, fmp_key)

if __name__ == "__main__":
    main()

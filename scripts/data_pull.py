#!/usr/bin/env python3
"""
Phase 2: Ingest Wilshire 5000 symbols + quotes & fundamentals (first 250 tickers),
explicitly loading service-account credentials from sa.json so no ADC errors.
"""

import os
import time
import csv
import requests
from google.cloud import bigquery, secretmanager_v1
from google.oauth2 import service_account

# ─── CONFIG ─────────────────────────────────────────────────────────────
PROJECT      = os.getenv("GCP_PROJECT", "tradesmith-458506")
DATASET      = "raw_market"
CSV_FILE     = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
MAX_TICKERS  = 250
FMP_BASE     = "https://financialmodelingprep.com/api/v3"
# The workflow writes your SA key here:
SA_JSON_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
# Secret Manager resource name:
FMP_SECRET = f"projects/{PROJECT}/secrets/FMP_API_KEY/versions/latest"
# ────────────────────────────────────────────────────────────────────────

def load_credentials():
    """Load service-account JSON from sa.json and return Credentials."""
    if not os.path.exists(SA_JSON_PATH):
        raise FileNotFoundError(f"{SA_JSON_PATH} not found. Did your workflow write it?")
    return service_account.Credentials.from_service_account_file(SA_JSON_PATH)

def get_fmp_key(creds):
    """Use Secret Manager client to fetch the FMP API key secret."""
    sm = secretmanager_v1.SecretManagerServiceClient(credentials=creds)
    resp = sm.access_secret_version(name=FMP_SECRET)
    return resp.payload.data.decode("utf-8").strip()

def load_symbols():
    """Read tickers from CSV; expects a header with 'symbol' column."""
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

def write_symbols(bq, symbols):
    """Stream the full CSV list into raw_market.symbols."""
    table = f"{PROJECT}.{DATASET}.symbols"
    rows = [{"symbol":s, "name":"", "exchange":""} for s in symbols]
    print(f"Inserting {len(rows)} symbols into {table}…")
    errs = bq.insert_rows_json(table, rows)
    if errs:
        print("⚠️ Symbol insert errors:", errs)
    else:
        print("✅ Symbols loaded")

def ingest_quotes(bq, tickers, fmp_key):
    """Fetch latest quote per ticker, write into quotes_intraday."""
    table = f"{PROJECT}.{DATASET}.quotes_intraday"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/quote/{t}?apikey={fmp_key}"
        r = requests.get(url); r.raise_for_status()
        data = r.json()
        if data:
            q = data[0]
            rows.append({
                "ticker": t,
                "ts":      q["timestamp"],
                "price":   q["price"],
                "volume":  q["volume"]
            })
        time.sleep(0.1)
    print(f"Inserting {len(rows)} quotes into {table}…")
    errs = bq.insert_rows_json(table, rows)
    if errs:
        print("⚠️ Quote insert errors:", errs)
    else:
        print("✅ Quotes loaded")

def ingest_fundamentals(bq, tickers, fmp_key):
    """Fetch profile per ticker, write into fundamentals_daily."""
    table = f"{PROJECT}.{DATASET}.fundamentals_daily"
    rows = []
    for t in tickers:
        url = f"{FMP_BASE}/profile/{t}?apikey={fmp_key}"
        r = requests.get(url); r.raise_for_status()
        data = r.json()
        if data:
            p = data[0]
            rows.append({
                "ticker":       t,
                "as_of_date":   p.get("priceDate"),
                "json_payload": p
            })
        time.sleep(0.1)
    print(f"Inserting {len(rows)} fundamentals into {table}…")
    errs = bq.insert_rows_json(table, rows)
    if errs:
        print("⚠️ Fundamentals insert errors:", errs)
    else:
        print("✅ Fundamentals loaded")

def main():
    # Load creds and clients
    creds = load_credentials()
    bq_client = bigquery.Client(project=PROJECT, credentials=creds)

    # Pull the FMP API key from Secret Manager
    fmp_key = get_fmp_key(creds)

    # Load & write Wilshire symbols
    symbols = load_symbols()
    write_symbols(bq_client, symbols)

    # Limit for detailed ingestion
    tickers = symbols[:MAX_TICKERS]
    print(f"Processing quotes & fundamentals for {len(tickers)} tickers…")

    # Ingest market data
    ingest_quotes(bq_client, tickers, fmp_key)
    ingest_fundamentals(bq_client, tickers, fmp_key)

if __name__ == "__main__":
    main()

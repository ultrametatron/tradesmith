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
SA_JSON_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
FMP_SECRET   = f"projects/{PROJECT}/secrets/FMP_API_KEY/versions/latest"
# ────────────────────────────────────────────────────────────────────────

def load_credentials():
    """Load service-account JSON from sa.json and return Credentials."""
    if not os.path.exists(SA_JSON_PATH):
        raise FileNotFoundError(f"{SA_JSON_PATH} not found.")
    return service_account.Credentials.from_service_account_file(SA_JSON_PATH)

def get_fmp_key(creds):
    """Fetch the FMP API key from Secret Manager."""
    sm_client = secretmanager_v1.SecretManagerServiceClient(credentials=creds)
    resp = sm_client.access_secret_version(name=FMP_SECRET)
    return resp.payload.data.decode("utf-8").strip()

def load_symbols():
    """Read tickers from CSV; expects a 'symbol' column."""
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

def write_symbols(bq_client, symbols):
    """Stream the full CSV list into raw_market.symbols."""
    table = f"{PROJECT}.{DATASET}.symbols"
    rows = [{"symbol": s, "name": "", "exchange": ""} for s in symbols]
    print(f"Inserting {len(rows)} symbols into {table}…")
    errs = bq_client.insert_rows_json(table, rows)
    if errs:
        print("⚠️ Symbol insert errors:", errs)
    else:
        print("✅ Symbols loaded")

def ingest_quotes(bq_client, tickers, fmp_key):
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
        time.sleep(0.1)
    print(f"Inserting {len(rows)} quotes into {table}…")
    errs = bq_client.insert_rows_json(table, rows)
    if errs:
        print("⚠️ Quote insert errors:", errs)
    else:
        print("✅ Quotes loaded")

def ingest_fundamentals(bq_client, tickers, fmp_key):
    """
    Fetch company profiles in batches (bulk endpoint) and write into fundamentals_daily.
    Reduces rate-limit errors by batching and doing exponential backoff on 429s.
    """
    table = f"{PROJECT}.{DATASET}.fundamentals_daily"
    rows = []
    batch_size = 50
    for start in range(0, len(tickers), batch_size):
        batch = tickers[start:start+batch_size]
        tickers_str = ",".join(batch)
        url = f"{FMP_BASE}/profile/{tickers_str}?apikey={fmp_key}"

        # retry loop for 429s
        for attempt in range(5):
            resp = requests.get(url)
            if resp.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f"⚠️ 429 on batch {start//batch_size+1}, sleeping {wait}s…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        else:
            raise RuntimeError(f"Failed to fetch profiles for batch starting at {start}")

        for profile in data:
            rows.append({
                "ticker":       profile.get("symbol"),
                "as_of_date":   profile.get("priceDate"),
                "json_payload": profile
            })

        time.sleep(1)  # pause between batches

    print(f"Inserting {len(rows)} fundamentals into {table}…")
    errs = bq_client.insert_rows_json(table, rows)
    if errs:
        print("⚠️ Fundamentals insert errors:", errs)
    else:
        print("✅ Fundamentals loaded")

def main():
    creds = load_credentials()
    bq_client = bigquery.Client(project=PROJECT, credentials=creds)
    fmp_key = get_fmp_key(creds)

    symbols = load_symbols()
    write_symbols(bq_client, symbols)

    tickers = symbols[:MAX_TICKERS]
    print(f"Processing quotes & fundamentals for {len(tickers)} tickers…")

    ingest_quotes(bq_client, tickers, fmp_key)
    ingest_fundamentals(bq_client, tickers, fmp_key)

if __name__ == "__main__":
    main()

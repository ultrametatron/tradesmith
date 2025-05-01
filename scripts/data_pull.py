#!/usr/bin/env python3
"""
Phase 2: Ingest Wilshire 5000 symbols + quotes & fundamentals,
explicitly loading service-account credentials from sa.json,
quoting first N tickers, and batching fundamentals in safe chunks.
"""

import os
import time
import csv
import json
import requests
import argparse
from google.cloud import bigquery, secretmanager_v1
from google.oauth2 import service_account

# ─── CONFIG (can be overridden via flags) ────────────────────────────────
DEFAULT_MAX_QUOTES     = 3500
DEFAULT_FUND_BATCH     = 100   # safe bulk‐profile limit per FMP docs
CSV_FILE               = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
PROJECT_ENV            = os.getenv("GCP_PROJECT", "tradesmith-458506")
SA_JSON_ENV            = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
FMP_SECRET_RESOURCE    = f"projects/{PROJECT_ENV}/secrets/FMP_API_KEY/versions/latest"
FMP_BASE               = "https://financialmodelingprep.com/api/v3"
# ────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--project-id", default=PROJECT_ENV)
    p.add_argument("--sa-json",    default=SA_JSON_ENV)
    p.add_argument("--csv-file",   default=CSV_FILE)
    p.add_argument("--max-quotes", type=int, default=DEFAULT_MAX_QUOTES)
    p.add_argument("--fund-batch", type=int, default=DEFAULT_FUND_BATCH)
    return p.parse_args()

def load_credentials(sa_json):
    if not os.path.exists(sa_json):
        raise FileNotFoundError(f"{sa_json} not found.")
    return service_account.Credentials.from_service_account_file(sa_json)

def get_fmp_key(creds, project):
    name = f"projects/{project}/secrets/FMP_API_KEY/versions/latest"
    sm = secretmanager_v1.SecretManagerServiceClient(credentials=creds)
    return sm.access_secret_version(name=name).payload.data.decode().strip()

def load_symbols(csv_file):
    syms = []
    with open(csv_file, newline="") as f:
        reader = csv.reader(f); header = next(reader)
        idx = header.index("symbol") if "symbol" in header else 0
        for row in reader:
            s = row[idx].strip().upper()
            if s: syms.append(s)
    return syms

def write_symbols(bq, project, dataset, symbols):
    table = f"{project}.{dataset}.symbols"
    rows = [{"symbol":s,"name":"","exchange":""} for s in symbols]
    print(f"Inserting {len(rows)} symbols into {table}…")
    errs = bq.insert_rows_json(table, rows)
    print("⚠️ Symbol errors:", errs) if errs else print("✅ Symbols loaded")

def ingest_quotes(bq, project, dataset, tickers, fmp_key):
    table = f"{project}.{dataset}.quotes_intraday"
    rows = []
    for t in tickers:
        resp = requests.get(f"{FMP_BASE}/quote/{t}?apikey={fmp_key}")
        resp.raise_for_status()
        data = resp.json()
        if data:
            q = data[0]
            rows.append({"ticker":t,"ts":q["timestamp"],"price":q["price"],"volume":q["volume"]})
        time.sleep(0.05)
    print(f"Inserting {len(rows)} quotes into {table}…")
    errs = bq.insert_rows_json(table, rows)
    print("⚠️ Quote errors:", errs) if errs else print("✅ Quotes loaded")

def ingest_fundamentals(bq, project, dataset, symbols, fmp_key, batch_size):
    table = f"{project}.{dataset}.fundamentals_daily"
    rows = []
    total = len(symbols)
    for start in range(0, total, batch_size):
        batch = symbols[start:start+batch_size]
        url = f"{FMP_BASE}/profile/{','.join(batch)}?apikey={fmp_key}"

        # exponential backoff for rate limits
        for attempt in range(6):
            resp = requests.get(url)
            if resp.status_code == 429:
                wait = (2 ** attempt) * 10
                print(f"⚠️ 429 (batch {start//batch_size+1}), waiting {wait}s…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        else:
            raise RuntimeError(f"Failed to fetch fundamentals batch at offset {start}")

        for p in data:
            rows.append({
                "ticker":       p.get("symbol"),
                "as_of_date":   p.get("priceDate"),
                "json_payload": json.dumps(p)
            })
        # gentle pause between batches
        time.sleep(5)

    print(f"Inserting {len(rows)} fundamentals into {table}…")
    errs = bq.insert_rows_json(table, rows)
    print("⚠️ Fundamental errors:", errs) if errs else print("✅ Fundamentals loaded")

def main():
    args     = parse_args()
    creds    = load_credentials(args.sa_json)
    project  = args.project_id
    dataset  = "raw_market"
    bq       = bigquery.Client(project=project, credentials=creds)
    fmp_key  = get_fmp_key(creds, project)

    symbols = load_symbols(args.csv_file)
    write_symbols(bq, project, dataset, symbols)

    qt = symbols[: args.max_quotes]
    print(f"Processing quotes for {len(qt)} tickers…")
    ingest_quotes(bq, project, dataset, qt, fmp_key)

    print(f"Processing fundamentals for {len(symbols)} tickers in batches of {args.fund_batch}…")
    ingest_fundamentals(bq, project, dataset, symbols, fmp_key, args.fund_batch)

if __name__ == "__main__":
    main()

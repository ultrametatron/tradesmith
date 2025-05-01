#!/usr/bin/env python3
"""
Daily Fundamentals Pull

Loads the entire Wilshire 5000 fundamentals into BigQuery in safe batches.
"""

import os
import time
import csv
import json
import requests
from google.cloud import bigquery, secretmanager_v1
from google.oauth2 import service_account

# ─── CONFIG ─────────────────────────────────────────────────────────────
PROJECT       = os.getenv("GCP_PROJECT", "tradesmith-458506")
DATASET       = "raw_market"
CSV_FILE      = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
FUND_BATCH    = 100           # adjust if needed; FMP bulk limit is ~100
FMP_BASE      = "https://financialmodelingprep.com/api/v3"
SA_JSON       = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
FMP_SECRET    = f"projects/{PROJECT}/secrets/FMP_API_KEY/versions/latest"
# ────────────────────────────────────────────────────────────────────────

def load_credentials():
    """Load service-account JSON from sa.json."""
    if not os.path.exists(SA_JSON):
        raise FileNotFoundError(f"{SA_JSON} not found.")
    return service_account.Credentials.from_service_account_file(SA_JSON)

def get_fmp_key(creds):
    """Fetch the FMP API key from Secret Manager."""
    sm = secretmanager_v1.SecretManagerServiceClient(credentials=creds)
    name = FMP_SECRET
    resp = sm.access_secret_version(name=name)
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

def ingest_fundamentals(bq, symbols, fmp_key):
    """
    Fetch company profiles in batches of FUND_BATCH and write into fundamentals_daily.
    """
    table = f"{PROJECT}.{DATASET}.fundamentals_daily"
    rows = []
    total = len(symbols)
    for start in range(0, total, FUND_BATCH):
        batch = symbols[start:start+FUND_BATCH]
        tickers_str = ",".join(batch)
        url = f"{FMP_BASE}/profile/{tickers_str}?apikey={fmp_key}"

        # exponential backoff for 429
        for attempt in range(6):
            resp = requests.get(url)
            if resp.status_code == 429:
                wait = (2 ** attempt) * 10
                print(f"⚠️ 429 on fundamentals batch {start//FUND_BATCH+1}, sleeping {wait}s…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        else:
            raise RuntimeError(f"Failed batch at offset {start}")

        for p in data:
            rows.append({
                "ticker":       p.get("symbol"),
                "as_of_date":   p.get("priceDate"),
                "json_payload": json.dumps(p)
            })

        time.sleep(5)  # pause between batches

    print(f"Inserting {len(rows)} fundamentals into {table}…")
    errors = bq.insert_rows_json(table, rows)
    if errors:
        print("⚠️ Fundamentals insert errors:", errors)
    else:
        print("✅ Fundamentals loaded")

def main():
    creds    = load_credentials()
    bq       = bigquery.Client(project=PROJECT, credentials=creds)
    fmp_key  = get_fmp_key(creds)
    symbols  = load_symbols()

    print(f"Processing fundamentals for {len(symbols)} tickers in batches of {FUND_BATCH}…")
    ingest_fundamentals(bq, symbols, fmp_key)

if __name__ == "__main__":
    main()

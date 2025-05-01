#!/usr/bin/env python3
"""
Phase 2: Ingest Wilshire 5000 + quotes & fundamentals,
retrieving FMP key from Secret Manager at runtime.
"""

import os, time, csv, requests, argparse
from google.cloud import bigquery, secretmanager

PROJECT = os.getenv("GCP_PROJECT", "tradesmith-458506")
DATASET = "raw_market"
CSV_FILE = os.path.join(os.path.dirname(__file__), "wilshire_5000.csv")
MAX_TICKERS = 250
FMP_SECRET_NAME = f"projects/{PROJECT}/secrets/FMP_API_KEY/versions/latest"

def get_fmp_key():
    client = secretmanager.SecretManagerServiceClient()
    resp = client.access_secret_version(name=FMP_SECRET_NAME)
    return resp.payload.data.decode("utf-8")

def load_symbols(path):
    syms = []
    with open(path, newline="") as f:
        reader = csv.reader(f); header = next(reader)
        idx = header.index("symbol") if "symbol" in header else 0
        for row in reader:
            s = row[idx].strip().upper()
            if s: syms.append(s)
    return syms

def write_symbols(bq, syms):
    tid = f"{PROJECT}.{DATASET}.symbols"
    rows = [{"symbol":s,"name":"","exchange":""} for s in syms]
    print(f"Inserting {len(rows)} symbols…")
    errs = bq.insert_rows_json(tid, rows)
    print("⚠️ Errors" if errs else "✅ Symbols loaded.", errs or "")

def ingest_quotes(bq, syms, key):
    tid = f"{PROJECT}.{DATASET}.quotes_intraday"
    rows = []
    for s in syms:
        url = f"https://financialmodelingprep.com/api/v3/quote/{s}?apikey={key}"
        data = requests.get(url).json()
        if data:
            q = data[0]
            rows.append({"ticker":s,"ts":q["timestamp"],"price":q["price"],"volume":q["volume"]})
        time.sleep(0.1)
    print(f"Inserting {len(rows)} quotes…")
    errs = bq.insert_rows_json(tid, rows)
    print("⚠️ Errors" if errs else "✅ Quotes loaded.", errs or "")

def ingest_fundamentals(bq, syms, key):
    tid = f"{PROJECT}.{DATASET}.fundamentals_daily"
    rows = []
    for s in syms:
        url = f"https://financialmodelingprep.com/api/v3/profile/{s}?apikey={key}"
        data = requests.get(url).json()
        if data:
            p = data[0]
            rows.append({"ticker":s,"as_of_date":p.get("priceDate"),"json_payload":p})
        time.sleep(0.1)
    print(f"Inserting {len(rows)} fundamentals…")
    errs = bq.insert_rows_json(tid, rows)
    print("⚠️ Errors" if errs else "✅ Fundamentals loaded.", errs or "")

def main():
    # 1) fetch secret
    fmp_key = get_fmp_key()

    # 2) load symbols
    syms = load_symbols(CSV_FILE)
    write_symbols(bigquery.Client(project=PROJECT), syms)

    # 3) ingest first N tickers
    subs = syms[:MAX_TICKERS]
    print(f"Running quotes/fundamentals for {len(subs)} tickers…")
    bq = bigquery.Client(project=PROJECT)
    ingest_quotes(bq, subs, fmp_key)
    ingest_fundamentals(bq, subs, fmp_key)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""
Phase 2: Ingest Wilshire 5000 symbols + intraday quotes & fundamentals (first 250 tickers).
"""

import os
import time
import csv
import requests
import argparse
from google.cloud import bigquery

def parse_args():
    p = argparse.ArgumentParser(
        description="Load Wilshire 5000 tickers, then ingest quotes & fundamentals into BigQuery"
    )
    p.add_argument(
        "--fmp-api-key",
        default=os.getenv("FMP_API_KEY"),
        help="FinancialModelingPrep API key (or set FMP_API_KEY env)"
    )
    p.add_argument(
        "--project-id",
        default=os.getenv("GCP_PROJECT"),
        help="GCP Project ID (or set GCP_PROJECT env)"
    )
    p.add_argument(
        "--dataset",
        default="raw_market",
        help="BigQuery dataset name"
    )
    p.add_argument(
        "--csv-file",
        default=os.path.join(os.path.dirname(__file__), "wilshire_5000.csv"),
        help="Path to CSV file listing tickers (header 'symbol')"
    )
    p.add_argument(
        "--max-tickers",
        type=int,
        default=250,
        help="Number of tickers to ingest quotes/fundamentals for"
    )
    args = p.parse_args()
    if not args.fmp_api_key:
        p.error("FMP API key required: pass --fmp-api-key or set FMP_API_KEY")
    if not args.project_id:
        p.error("GCP project ID required: pass --project-id or set GCP_PROJECT")
    return args

def load_symbols(csv_path):
    """Read tickers from CSV; expects a 'symbol' column in header."""
    syms = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        try:
            idx = header.index("symbol")
        except ValueError:
            idx = 0
        for row in reader:
            s = row[idx].strip().upper()
            if s:
                syms.append(s)
    return syms

def write_symbols(bq, project, dataset, symbols):
    """Stream symbol list into raw_market.symbols."""
    table_id = f"{project}.{dataset}.symbols"
    rows = [{"symbol": s, "name": "", "exchange": ""} for s in symbols]
    print(f"Inserting {len(rows)} symbols into {table_id} …")
    errs = bq.insert_rows_json(table_id, rows)
    if errs:
        print("⚠️ Symbol insert errors:", errs)
    else:
        print("✅ Symbols loaded")

def ingest_quotes(bq, project, dataset, tickers, api_key):
    """Fetch latest quote per ticker, load into quotes_intraday."""
    table_id = f"{project}.{dataset}.quotes_intraday"
    rows = []
    for t in tickers:
        url = f"https://financialmodelingprep.com/api/v3/quote/{t}?apikey={api_key}"
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
    print(f"Inserting {len(rows)} quotes into {table_id} …")
    errs = bq.insert_rows_json(table_id, rows)
    if errs:
        print("⚠️ Quote insert errors:", errs)
    else:
        print("✅ Quotes loaded")

def ingest_fundamentals(bq, project, dataset, tickers, api_key):
    """Fetch profile per ticker, load into fundamentals_daily."""
    table_id = f"{project}.{dataset}.fundamentals_daily"
    rows = []
    for t in tickers:
        url = f"https://financialmodelingprep.com/api/v3/profile/{t}?apikey={api_key}"
        r = requests.get(url); r.raise_for_status()
        data = r.json()
        if data:
            prof = data[0]
            rows.append({
                "ticker":       t,
                "as_of_date":   prof.get("priceDate"),
                "json_payload": prof
            })
        time.sleep(0.1)
    print(f"Inserting {len(rows)} fundamentals into {table_id} …")
    errs = bq.insert_rows_json(table_id, rows)
    if errs:
        print("⚠️ Fundamentals insert errors:", errs)
    else:
        print("✅ Fundamentals loaded")

def main():
    args = parse_args()

    # BigQuery client
    bq = bigquery.Client(project=args.project_id)

    # 1) Load & write Wilshire symbols
    symbols = load_symbols(args.csv_file)
    write_symbols(bq, args.project_id, args.dataset, symbols)

    # 2) Restrict to first N tickers for detailed ingest
    tickers = symbols[: args.max_tickers]
    print(f"Processing quotes & fundamentals for {len(tickers)} tickers…")

    ingest_quotes(bq, args.project_id, args.dataset, tickers, args.fmp_api_key)
    ingest_fundamentals(bq, args.project_id, args.dataset, tickers, args.fmp_api_key)

if __name__ == "__main__":
    main()

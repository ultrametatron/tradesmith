"""
run_intraday.py

Main intraday trading engine for TradeSmith (global branch).
Runs every 10 minutes to:
 1. Generate universe from master_tickers.csv
 2. Update market and fundamental data from IEX
 3. Select top 250 candidates by composite score
 4. Merge holdings with current prices to compute position values
 5. Fetch recent headlines for each ticker via NewsAPI
 6. Score sentiment using local DistilBERT
 7. Build LLM prompt and call o4-mini for trade adjustments
 8. Apply simulated trades and log commissions
 9. Append portfolio value to equity log
"""

import os
import time
import requests
import pandas as pd

from dynamic_universe import dynamic_universe_all
from update_master_prices import update_master
from select_candidates import select
from data_pull import pull
from sentiment_stream import score
from build_prompt import build_daily
from call_tradesmith import ask_trades
from apply_change import apply
from log_kpis import log

# NewsAPI configuration
NEWS_KEY = os.getenv("NEWS_API_KEY")
NEWS_URL = "https://newsapi.org/v2/everything"

def fetch_headlines(symbol: str, n: int = 10) -> list:
    """
    Fetch up to n recent headlines for `symbol` from NewsAPI.
    Returns a list of headline strings; returns empty list on error or missing key.
    """
    if not NEWS_KEY:
        return []
    params = {
        "q": symbol,
        "apiKey": NEWS_KEY,
        "pageSize": n,
        "sortBy": "publishedAt",
        "language": "en",
    }
    try:
        resp = requests.get(NEWS_URL, params=params, timeout=5)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [a.get("title", "") for a in articles[:n]]
    except Exception:
        # If NewsAPI call fails, return empty headlines
        return []

def main():
    # 1) Universe generation: write top 5,000 tickers to CSV
    symbols = dynamic_universe_all(5000)
    pd.DataFrame({"Symbol": symbols}).to_csv("state/master_tickers.csv", index=False)

    # 2) Update market & company data from IEX
    update_master()

    # 3) Select top 250 candidates by composite score
    select(250)

    # 4) Merge holdings with candidate data; compute current position values
    df = pull()

    # 5) Fetch and score sentiment for each ticker
    sentiments = []
    for sym in df.Symbol:
        headlines = fetch_headlines(sym, n=10)
        if headlines:
            avg_score = sum(score(h) for h in headlines) / len(headlines)
        else:
            avg_score = 0.0
        sentiments.append(avg_score)
        time.sleep(0.1)  # avoid hitting NewsAPI rate limits
    df["Sentiment"] = sentiments

    # 6) Build the daily prompt and request trade adjustments
    prompt = build_daily(df)
    adjustments = ask_trades(prompt)

    # 7) Apply simulated trades and log commissions
    apply(adjustments.get("adjustments", []))

    # 8) Log current portfolio value to equity log
    log(df)

if __name__ == "__main__":
    main()

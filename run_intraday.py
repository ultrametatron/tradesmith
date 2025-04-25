"""
Main intraday engine: runs every 10 minutes (Mon–Fri).
"""
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

def fetch_headlines(symbol: str, n: int = 10) -> list:
    # Replace with real news-API fetch
    return [f"{symbol} headline {i}" for i in range(1, n+1)]

def main():
    # 1) Universe
    syms = dynamic_universe_all()
    pd.DataFrame({"Symbol": syms}).to_csv("state/master_tickers.csv", index=False)

    # 2) Data pull
    update_master()

    # 3) Candidate ranking
    select()

    # 4) Merge & compute values
    df = pull()

    # 5) Sentiment for each ticker
    df["Sentiment"] = df.Symbol.apply(
        lambda s: sum(score(h) for h in fetch_headlines(s, 10)) / 10
    )

    # 6) Build prompt & ask model for trades
    prompt = build_daily(df)
    res = ask_trades(prompt)

    # 7) Apply simulated trades & log commissions
    apply(res["adjustments"])

    # 8) Log portfolio value
    log(df)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
run_intraday.py

1. Update full master_prices.csv (daily metrics via FMP history).
2. Select top N candidates (writes state/top250.csv).
3. Refresh live prices for those top N (writes state/top250_live.csv).
4. Build prompt, call LLM for adjustments, apply to virtual portfolio, log P&L.
"""

import os
import sys
import datetime
import pandas as pd

from update_master_prices import update_master      # daily metrics
from select_candidates import select                # top-N selector
from update_top250_live import update_top250_live  # refresh quotes
from call_tradesmith import ask_trades              # LLM adjustment

STATE_DIR = "state"
TOP_N     = 250

def main():
    # 1) Ensure metrics are up to date
    update_master()  
    print("master_prices.csv up-to-date")

    # 2) Pick top N
    select(TOP_N)
    print(f"top{TOP_N}.csv generated")

    # 3) Refresh live quotes for those top N
    update_top250_live()
    print("top250_live.csv generated")

    # 4) Load the live snapshot
    df_live = pd.read_csv(os.path.join(STATE_DIR, "top250_live.csv"))

    # 5) Build the prompt for the LLM
    #    (your build_prompt should accept df_live)
    from build_prompt import build_prompt  
    prompt = build_prompt(df_live)

    # 6) Ask the LLM for adjustments
    try:
        adjustments = ask_trades(prompt)
    except Exception as e:
        print(f"❌ ask_trades failed: {e}")
        adjustments = {}

    # 7) Apply adjustments (your existing logic)
    from apply_adjustments import apply_adjustments
    holdings, pnl = apply_adjustments(df_live, adjustments)

    # 8) Log P&L
    log_path = os.path.join(STATE_DIR, "equity_curve.csv")
    df_log = pd.DataFrame(pnl)
    df_log.to_csv(log_path, mode="a", header=not os.path.exists(log_path), index=False)
    print(f"P&L appended to {log_path}")

if __name__ == "__main__":
    main()

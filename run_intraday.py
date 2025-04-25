#!/usr/bin/env python
"""
run_intraday.py

1. Exit outside US trading hours (pre/regular/post-market ET)
2. Update full master_prices.csv (daily metrics via FMP history).
3. Select top N candidates (state/top250.csv).
4. Refresh live quotes for those top N (state/top250_live.csv).
5. Build prompt, call LLM for adjustments, apply adjustments, log P&L.
"""

import os
import sys
import datetime
import pandas as pd

from pytz import timezone
from update_master_prices import update_master    # daily metrics
from select_candidates import select              # top-N selector
from update_top250_live import update_top250_live  # refresh quotes
from call_tradesmith import ask_trades            # LLM adjustment
from build_prompt import build_prompt
from apply_adjustments import apply_adjustments

# ── Configuration ────────────────────────────────────────────────────────────────
STATE_DIR = "/data/state"
TOP_N     = 250
# ─────────────────────────────────────────────────────────────────────────────────

def in_us_trading_hours() -> bool:
    tz = timezone("America/New_York")
    now = datetime.datetime.now(tz)
    h, m, wd = now.hour, now.minute, now.weekday()  # Mon=0…Fri=4
    if wd > 4:
        return False
    pre = (4 <= h < 9) or (h == 9 and m < 30)
    reg = (h == 9 and m >= 30) or (10 <= h < 16)
    post = (16 <= h < 20)
    return pre or reg or post

def main():
    # 0) Guard: only run within US trading windows
    if not in_us_trading_hours():
        print("Outside US trading hours; exiting.")
        sys.exit(0)

    # 1) Ensure full‐universe metrics are up to date
    update_master()
    print("✅ master_prices.csv updated")

    # 2) Compute top-N candidates
    select(TOP_N)
    print(f"✅ state/top{TOP_N}.csv generated")

    # 3) Refresh live quotes for those top N
    update_top250_live()
    print("✅ state/top250_live.csv generated")

    # 4) Load live snapshot
    df_live = pd.read_csv(os.path.join(STATE_DIR, "top250_live.csv"))

    # 5) Build prompt
    prompt = build_prompt(df_live)

    # 6) Ask LLM for adjustments
    try:
        adjustments = ask_trades(prompt)
    except Exception as e:
        print(f"❌ ask_trades failed: {e}")
        adjustments = {}

    # 7) Apply adjustments
    try:
        holdings, pnl = apply_adjustments(df_live, adjustments)
    except Exception as e:
        print(f"❌ apply_adjustments failed: {e}")
        holdings, pnl = None, []

    # 8) Log P&L to equity_curve.csv
    log_path = os.path.join(STATE_DIR, "equity_curve.csv")
    df_log = pd.DataFrame(pnl)
    os.makedirs(STATE_DIR, exist_ok=True)
    df_log.to_csv(log_path, mode="a", header=not os.path.exists(log_path), index=False)
    print(f"✅ P&L appended to {log_path}")

if __name__ == "__main__":
    main()

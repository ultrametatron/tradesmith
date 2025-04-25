#!/usr/bin/env python
import os, sys, datetime
import pandas as pd
from pytz import timezone

from update_master_prices import update_master
from select_candidates import select
from update_top250_live import update_top250_live
from build_prompt import build_prompt
from call_tradesmith import ask_trades
from apply_adjustments import apply_adjustments

STATE_DIR = "/data/state"
TOP_N     = 250

def in_us_trading_hours():
    tz = timezone("America/New_York")
    now = datetime.datetime.now(tz)
    h, m, wd = now.hour, now.minute, now.weekday()
    if wd > 4: return False
    pre = (4 <= h < 9) or (h == 9 and m < 30)
    reg = (h == 9 and m >= 30) or (10 <= h < 16)
    post= (16 <= h < 20)
    return pre or reg or post

def main():
    if not in_us_trading_hours():
        print("Outside US trading hours; exiting."); sys.exit(0)

    os.makedirs(STATE_DIR, exist_ok=True)
    update_master(); print("master_prices.csv updated")
    select(TOP_N);    print(f"top{TOP_N}.csv generated")
    update_top250_live(); print("top250_live.csv generated")

    df_live = pd.read_csv(f"{STATE_DIR}/top250_live.csv")
    prompt  = build_prompt(df_live)

    try:
        adjustments = ask_trades(prompt)
    except Exception as e:
        print(f"ask_trades failed: {e}"); adjustments = {}

    try:
        holdings, pnl = apply_adjustments(df_live, adjustments)
    except Exception as e:
        print(f"apply_adjustments failed: {e}"); pnl = []

    log_path = f"{STATE_DIR}/equity_curve.csv"
    df_log = pd.DataFrame(pnl)
    df_log.to_csv(log_path, mode="a", header=not os.path.exists(log_path), index=False)
    print(f"P&L appended to {log_path}")

if __name__ == "__main__":
    main()

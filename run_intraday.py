#!/usr/bin/env python
"""
run_intraday.py

Main intraday orchestration:
- Fetch live quotes for all 3500+ tickers
- Merge onto static master metrics
- Compute contextual features
- Recalculate composite scores & select Top 250
- Generate LLM prompt & apply adjustments
- Throttled RL-Light weight update
"""

import os
import time
import logging
from datetime import datetime
import pandas as pd

from call_tradesmith import ask_trades
from build_prompt import build_prompt
from apply_adjustments import apply_adjustments, log_equity_curve
from update_top250_live import fetch_prices
from select_candidates import select
from rl_light_throttled import update_weights_throttled

# ── Config ───────────────────────────────────────────────────────────────────────
STATE_DIR          = "/data/state"
MASTER_FILE        = os.path.join(STATE_DIR, "master_prices.csv")
TOP250_LIVE_FILE   = os.path.join(STATE_DIR, "top250_live.csv")

MAX_RETRIES        = 2      # number of fetch_prices retry attempts
RETRY_DELAY        = 5      # seconds between retries
# ────────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def dynamic_intraday_cycle():
    start = time.time()
    logging.info("=== Starting intraday cycle ===")

    # ensure state dir
    os.makedirs(STATE_DIR, exist_ok=True)

    # 1. load master metrics
    if not os.path.exists(MASTER_FILE):
        logging.error("Master file missing: %s", MASTER_FILE)
        return
    df_master = pd.read_csv(MASTER_FILE)
    symbols   = df_master["Symbol"].astype(str).tolist()
    logging.info("Loaded master for %d symbols", len(symbols))

    # 2. fetch live with retry
    for i in range(1, MAX_RETRIES+1):
        try:
            t0 = time.time()
            df_prices = fetch_prices(symbols)
            logging.info(
                "Fetched %d live quotes (try %d) in %.2fs",
                len(symbols), i, time.time() - t0
            )
            break
        except Exception as e:
            logging.warning("Fetch attempt %d failed: %s", i, e)
            if i < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logging.error("All fetch attempts failed; aborting")
                return

    # 3. merge & compute context
    try:
        df_live = df_master.merge(df_prices, on="Symbol", how="left")
        logging.info("Merged live onto master metrics")
        # --- Context features ---
        now = datetime.utcnow()
        hour = now.hour + now.minute/60
        if hour < 13:
            bucket = "pre_open"
        elif hour < 20:  # 13–20 UTC = 9:00–16:00 ET
            bucket = "open_hours"
        else:
            bucket = "post_close"
        df_live["time_bucket"]   = bucket
        df_live["vol_imbalance"] = df_live["volume"] / df_live["avgVolume"]
        logging.info("Added context: time_bucket=%s, vol_imbalance", bucket)
    except Exception as e:
        logging.error("Error merging/context: %s", e)
        return

    # 4. snapshot
    try:
        df_live.to_csv(TOP250_LIVE_FILE, index=False)
        logging.info("Saved live snapshot to %s", TOP250_LIVE_FILE)
    except Exception as e:
        logging.error("Error saving snapshot: %s", e)
        return

    # 5. select Top 250
    try:
        select(top_n=250)
        logging.info("Selected Top 250")
    except Exception as e:
        logging.error("Selection error: %s", e)
        return

    # 6. build prompt
    try:
        prompt = build_prompt()
        logging.info("Prompt built")
    except Exception as e:
        logging.error("Prompt error: %s", e)
        return

    # 7. LLM call
    try:
        adjustments = ask_trades(prompt)
        logging.info("Received %d instructions",
                     len(adjustments) if isinstance(adjustments, list) else 1)
    except Exception as e:
        logging.error("LLM call failed: %s", e)
        return

    # 8. apply & log
    try:
        apply_adjustments(adjustments)
        log_equity_curve()
        logging.info("Adjustments applied & equity curve logged")
    except Exception as e:
        logging.error("Apply/log error: %s", e)

    # 9. throttled RL-Light update
    try:
        info = update_weights_throttled()
        if info.get("skipped"):
            logging.info("RL update skipped (interval %d)", info["intervals"])
        else:
            logging.info("RL update done: intervals=%d window=%d reward=%.4f",
                         info["intervals"], info["window"], info["reward"])
    except Exception as e:
        logging.error("RL update error: %s", e)

    logging.info("=== Cycle completed in %.2f s ===", time.time() - start)

def main():
    dynamic_intraday_cycle()

if __name__ == "__main__":
    main()
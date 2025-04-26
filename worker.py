#!/usr/bin/env python
import os
import shutil
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone

# ── Paths ───────────────────────────────────────────────────────────────────────
HERE      = os.path.dirname(__file__)
SEED_DIR  = os.path.join(HERE, "seed")
STATE_DIR = "/data/state"
# ────────────────────────────────────────────────────────────────────────────────

def bootstrap_state():
    """
    Copy any seed CSVs from /app/seed into /data/state if they don't already exist.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    for fname in os.listdir(SEED_DIR):
        src = os.path.join(SEED_DIR, fname)
        dst = os.path.join(STATE_DIR, fname)
        if not os.path.exists(dst):
            logging.info(f"Seeding {dst} from {src}")
            shutil.copy(src, dst)

def in_us_trading_hours():
    """
    Return True if current time in New York is within pre/regular/post market.
    """
    tz = timezone("America/New_York")
    now = tz.localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC").localize(timezone("UTC"))))))))))))))
    h, m, wd = now.hour, now.minute, now.weekday()
    if wd > 4:
        return False
    pre  = (4 <= h < 9) or (h == 9 and m < 30)
    reg  = (h == 9 and m >= 30) or (10 <= h < 16)
    post = (16 <= h < 20)
    return pre or reg or post

def main():
    # 0) Guard: only run within US trading windows
    if not in_us_trading_hours():
        logging.info("Outside US trading hours; skipping run.")
        return

    # Import your intraday logic
    from run_intraday import main as intraday_main

    try:
        intraday_main()
    except Exception:
        logging.exception("Intraday run failed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # 1) Bootstrap seeded CSVs into persistent state
    bootstrap_state()

    # 2) Do one immediate run
    main()

    # 3) Schedule recurring runs every 15 min ET
    scheduler = BlockingScheduler(timezone="America/New_York")
    scheduler.add_job(
        main,
        trigger="cron",
        day_of_week="mon-fri",
        hour="4-19",
        minute="*/15",
        id="intraday_job",
        max_instances=1
    )
    scheduler.start()

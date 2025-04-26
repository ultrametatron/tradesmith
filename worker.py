#!/usr/bin/env python
import os
import shutil
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
import datetime
import sys

# ── Paths ───────────────────────────────────────────────────────────────────────
HERE      = os.path.dirname(__file__)
SEED_DIR  = os.path.join(HERE, "seed")
STATE_DIR = "/data/state"
# ────────────────────────────────────────────────────────────────────────────────

def bootstrap_state():
    """
    Copy seed CSVs from /app/seed into /data/state if they don't already exist.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    for fname in os.listdir(SEED_DIR):
        src = os.path.join(SEED_DIR, fname)
        dst = os.path.join(STATE_DIR, fname)
        if not os.path.exists(dst):
            logging.info(f"Seeding {dst} from {src}")
            shutil.copy(src, dst)

def in_us_trading_hours() -> bool:
    """
    True if now (NY time) is in pre-market 4:00–9:29, market 9:30–16:00, or
    post-market 16:00–20:00, Mon–Fri.
    """
    tz_ny = timezone("America/New_York")
    now   = datetime.datetime.now(tz_ny)
    h, m, wd = now.hour, now.minute, now.weekday()  # Mon=0…Fri=4
    if wd > 4:
        return False
    pre  = (4 <= h < 9) or (h == 9 and m < 30)
    reg  = (h == 9 and m >= 30) or (10 <= h < 16)
    post = (16 <= h < 20)
    return pre or reg or post

def main():
    # 0) Only run during US trading windows
    if not in_us_trading_hours():
        logging.info("Outside US trading hours; skipping run.")
        return

    # 1) Import and invoke your existing intraday logic
    try:
        from run_intraday import main as intraday_main
    except ImportError as e:
        logging.error(f"Could not import run_intraday: {e}")
        return

    try:
        intraday_main()
    except Exception:
        logging.exception("Intraday run failed")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # 1) Bootstrap seeds → persistent disk
    bootstrap_state()

    # 2) One immediate run
    main()

    # 3) Schedule every 15 min, Mon–Fri, ET 04:00–19:59
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

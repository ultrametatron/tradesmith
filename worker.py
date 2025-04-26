#!/usr/bin/env python
import os
import shutil
import logging
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone

# ── Paths ───────────────────────────────────────────────────────────────────────
HERE            = os.path.dirname(__file__)
CODE_STATE_DIR  = os.path.join(HERE, "state")       # your repo-tracked folder
DISK_STATE_DIR  = "/data/state"                     # your Render Disk mount
# ────────────────────────────────────────────────────────────────────────────────

def bootstrap_state():
    """
    Copy all files from repo's state/ folder into the persistent disk at /data/state
    if they don't already exist there.
    """
    os.makedirs(DISK_STATE_DIR, exist_ok=True)

    if not os.path.isdir(CODE_STATE_DIR):
        logging.warning(f"Repo state dir not found at {CODE_STATE_DIR}; skipping bootstrap.")
        return

    for fname in os.listdir(CODE_STATE_DIR):
        src = os.path.join(CODE_STATE_DIR, fname)
        dst = os.path.join(DISK_STATE_DIR, fname)
        if not os.path.exists(dst):
            logging.info(f"Seeding {dst} from {src}")
            shutil.copy(src, dst)

def in_us_trading_hours() -> bool:
    """
    Return True if now (Eastern Time) is within:
      - Pre-market:   04:00–09:29
      - Regular:      09:30–16:00
      - Post-market:  16:00–20:00
    on a Monday–Friday.
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
    # 0) Only proceed if within US trading hours
    if not in_us_trading_hours():
        logging.info("Outside US trading hours; skipping run.")
        return

    # 1) Import and run your intraday logic
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

    # 1) Bootstrap seed files into persistent disk
    bootstrap_state()

    # 2) Run once immediately on startup
    main()

    # 3) Schedule recurring runs every 15 minutes, Mon–Fri, ET 04:00–19:59
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

#!/usr/bin/env python
# worker.py

import os
import time
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from run_intraday import dynamic_intraday_cycle
from update_master_prices import update_master  # ensure this writes to /data/state

# ── Config ────────────────────────────────────────────────────────────
# Intraday: every 15 min, Mon–Fri, between 4:00–19:00 UTC (i.e. 00:00–15:00 ET)
INTRADAY_CRON = {
    'day_of_week': 'mon-fri',
    'hour': '4-19',
    'minute': '*/15'
}
# Daily master refresh: Mon–Fri at 11:00 UTC
DAILY_CRON = {
    'day_of_week': 'mon-fri',
    'hour': '11',
    'minute': '0'
}
# ─────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def start_scheduler():
    scheduler = BlockingScheduler(timezone="UTC")

    # Intraday job
    scheduler.add_job(
        dynamic_intraday_cycle,
        'cron',
        **INTRADAY_CRON,
        id='intraday_cycle'
    )
    logging.info("Scheduled intraday cycle: %s", INTRADAY_CRON)

    # Daily master-metrics job
    scheduler.add_job(
        update_master,
        'cron',
        **DAILY_CRON,
        id='daily_master_refresh'
    )
    logging.info("Scheduled daily master refresh: %s", DAILY_CRON)

    logging.info("Starting scheduler…")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.")

if __name__ == "__main__":
    # Ensure state directory exists for both jobs
    os.makedirs("/data/state", exist_ok=True)
    start_scheduler()
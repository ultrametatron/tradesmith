#!/usr/bin/env python
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
import datetime
import sys

# Import your existing intraday main routine
from run_intraday import main as intraday_main

def setup_scheduler():
    sched = BlockingScheduler(timezone="America/New_York")
    # Intraday job: every 15 min, Mon–Fri, ET 04:00–19:59
    sched.add_job(
        intraday_main,
        trigger="cron",
        day_of_week="mon-fri",
        hour="4-19",
        minute="*/15",
        id="intraday_job",
        max_instances=1
    )
    return sched

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Run once immediately on startup
    try:
        intraday_main()
    except Exception as e:
        logging.error(f"Startup run failed: {e}")
    # Then start the scheduler loop
    scheduler = setup_scheduler()
    scheduler.start()

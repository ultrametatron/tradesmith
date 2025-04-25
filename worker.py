#!/usr/bin/env python
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
import datetime
import sys

# Import your existing main() from run_intraday.py
from run_intraday import main as intraday_main

def setup_scheduler():
    sched = BlockingScheduler(timezone="America/New_York")

    # Intraday: every 15 min, Mon–Fri, hours 4:00–19:59 ET
    sched.add_job(
        intraday_main,
        trigger="cron",
        day_of_week="mon-fri",
        hour="4-19",
        minute="*/15

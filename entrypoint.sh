#!/usr/bin/env bash
set -e

# Decide which script to run by the Render service name
case "$RENDER_SERVICE_NAME" in
  *intraday*)
    exec python run_intraday.py
    ;;
  *daily-report*)
    exec python run_report.py
    ;;
  *weekly-report*)
    exec python run_weekly.py
    ;;
  *)
    echo "Unknown service name: $RENDER_SERVICE_NAME" >&2
    exit 1
    ;;
esac

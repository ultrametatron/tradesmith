"""
apply_adjustments.py

Takes live snapshot + adjustments dict, applies them to virtual holdings,
computes P&L, and logs to equity_curve.csv.
"""

import pandas as pd
from typing import Tuple, List, Dict
import os, csv

# Directory & file for equity curve logs
STATE_DIR = "/data/state"
EQUITY_CURVE_FILE = os.path.join(STATE_DIR, "equity_curve.csv")


def apply_adjustments(
    df_live: pd.DataFrame,
    adjustments: Dict[str, float]
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    - df_live: DataFrame of top250_live.csv with current holdings in 'Weight' column
    - adjustments: { symbol: new_weight, ... }

    Returns:
    - updated holdings DataFrame
    - list of P&L log dicts for each period:
      { timestamp, symbol, old_weight, new_weight, pnl }
    """
    # Copy and apply new weights
    df = df_live.copy()
    df["OldWeight"] = df["Weight"]
    df["NewWeight"] = df["Symbol"].map(adjustments).fillna(df["Weight"])
    df["P&L"] = (df["NewWeight"] - df["OldWeight"]) * df["Price"]

    # Build P&L log
    ts = pd.Timestamp.utcnow()
    pnl_log: List[Dict] = []
    for _, r in df.iterrows():
        pnl_log.append({
            "timestamp": ts,
            "symbol":   r.Symbol,
            "old_weight":  r.OldWeight,
            "new_weight":  r.NewWeight,
            "pnl":      r["P&L"]
        })

    return df, pnl_log


def log_equity_curve(pnl_log: List[Dict]):
    """
    Append P&L log entries to equity_curve.csv.
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    file_exists = os.path.isfile(EQUITY_CURVE_FILE)
    with open(EQUITY_CURVE_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pnl_log[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(pnl_log)
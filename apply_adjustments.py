"""
apply_adjustments.py

Takes live snapshot + adjustments dict, applies them to virtual holdings,
and computes P&L.
"""

import pandas as pd
from typing import Tuple, List, Dict

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
    pnl_log = []
    for _, r in df.iterrows():
        pnl_log.append({
            "timestamp": ts,
            "symbol":    r.Symbol,
            "old_weight":r.OldWeight,
            "new_weight":r.NewWeight,
            "pnl":       r["P&L"]
        })

    return df, pnl_log

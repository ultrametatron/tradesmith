"""
Deterministic helper functions for the LLM.
"""
import numpy as np

def compute_drawdown(values):
    """Return max drawdown (0–1) of a value series."""
    peak, max_dd = -np.inf, 0.0
    for v in values:
        peak = max(peak, v)
        if peak:
            max_dd = max(max_dd, (peak - v) / peak)
    return {"drawdown": max_dd}

def score_liquidity(volume, avg_volume):
    """Return liquidity score (0–1)."""
    if not avg_volume:
        return {"liquidity": 0.0}
    return {"liquidity": min(volume / avg_volume, 1.0)}

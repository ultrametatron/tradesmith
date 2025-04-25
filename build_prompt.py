"""
build_prompt.py

Converts the live DataFrame into a system prompt for the LLM.
"""

import pandas as pd

def build_prompt(df: pd.DataFrame) -> str:
    """
    Given df with columns Symbol, Price, ChangePct, MA50, MA200, YTDChange, DividendYield, etc.,
    produce a system‐role prompt for the trading‐adjustment function.
    """
    lines = ["You are TradeSmith, a portfolio coach. Here are the current holdings:"]
    lines.append("Symbol | Price | Change% | MA50 | MA200 | YTD% | DivYield")
    for _, row in df.iterrows():
        lines.append(
            f"{row.Symbol} | "
            f"{row.Price:.2f} | {row.ChangePct:.2%} | "
            f"{row.MA50 or 0:.2f} | {row.MA200 or 0:.2f} | "
            f"{row.YTDChange or 0:.2%} | {row.DividendYield or 0:.2%}"
        )
    lines.append(
        "Return a JSON object with 'symbol' and 'new_weight' for each adjustment, "
        "ensuring max 25% sector exposure and max 5% turnover."
    )
    return "\n".join(lines)

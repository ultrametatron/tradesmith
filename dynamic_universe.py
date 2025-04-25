"""
Generate the global ticker universe for main branch.
"""
import pandas as pd

def dynamic_universe_all(n=5000):
    # Read the master list and return top-n symbols
    return pd.read_csv("state/master_tickers.csv").Symbol.head(n).tolist()

"""
Merge current holdings with market data and compute position values.
"""
import pandas as pd, datetime

def pull():
    holdings = pd.read_csv("state/holdings.csv")
    candidates = pd.read_csv("state/top250.csv")
    df = holdings.merge(candidates, on="Symbol", how="left")
    df["Value"] = df["Shares"] * df["Price"]
    df["Date"] = datetime.datetime.utcnow()
    return df

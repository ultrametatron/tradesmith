"""
Fetch numeric & categorical fields in batches from IEX.
"""
import pandas as pd, requests, os, datetime, time

IEX_TOKEN = os.getenv("IEX_TOKEN")
BATCH = 100

def _fetch_batch(symbols):
    url = "https://cloud.iexapis.com/stable/stock/market/batch"
    params = {
        "symbols": ",".join(symbols),
        "types":   "quote,company",
        "token":   IEX_TOKEN
    }
    try:
        resp = requests.get(url, params=params, timeout=10).json()
    except Exception as e:
        raise RuntimeError("IEX batch request failed") from e

    rows = []
    for sym, data in resp.items():
        q, c = data["quote"], data["company"]
        rows.append({
            "Symbol":        sym,
            "Price":         q["latestPrice"],
            "Timestamp":     datetime.datetime.utcnow(),
            "ChangePct":     q["changePercent"],
            "Volume":        q["volume"],
            "MA50":          q.get("iexClose"),
            "MA200":         q.get("week52High"),
            "Beta":          q.get("beta"),
            "PERatio":       q.get("peRatio"),
            "PBRatio":       (q.get("peRatio") or 0)/2,
            "YTDChange":     q.get("ytdChange"),
            "DividendYield": q.get("dividendYield"),
            "Sector":        c.get("sector"),
            "Industry":      c.get("industry"),
            "Country":       c.get("country"),
            "MarketCap":     q.get("marketCap")
        })
    return rows

def update_master():
    # Read universe and fetch in batches
    tickers = pd.read_csv("state/master_tickers.csv").Symbol.tolist()
    all_rows = []
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i+BATCH]
        all_rows.extend(_fetch_batch(batch))
        time.sleep(0.1)  # avoid rate limits
    pd.DataFrame(all_rows).to_csv("state/master_prices.csv", index=False)

if __name__ == "__main__":
    update_master()

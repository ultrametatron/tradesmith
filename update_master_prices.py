"""
update_master_prices.py

Single-pass over the universe in 500-symbol batches:
  • Batch /quote and /profile calls
  • Per-symbol /historical-price-full to compute MA50, MA200, YTDChange
  • Write state/master_prices.csv with all metrics
"""

import os, time, datetime, requests, pandas as pd

FMP_KEY    = os.getenv("FMP_API_KEY") or RuntimeError("FMP_API_KEY required")
BASE_URL   = "https://financialmodelingprep.com/api/v3"
BATCH_SIZE = 500
HIST_DAYS  = 365

def fetch_prices(batch):
    url = f"{BASE_URL}/quote/{','.join(batch)}"
    j = requests.get(url, params={"apikey":FMP_KEY}).json()
    now = datetime.datetime.utcnow()
    return [{
        "Symbol": d["symbol"],
        "Price": d.get("price",0),
        "ChangePct": ((d.get("price",0)-d.get("previousClose",0))/
                      (d.get("previousClose") or 1)),
        "Volume": d.get("volume",0),
        "Timestamp": now
    } for d in j]

def fetch_profiles(batch):
    url = f"{BASE_URL}/profile/{','.join(batch)}"
    j = requests.get(url, params={"apikey":FMP_KEY}).json()
    return [{
        "Symbol":    d["symbol"],
        "Sector":    d.get("sector"),
        "Industry":  d.get("industry"),
        "Country":   d.get("country"),
        "MarketCap": d.get("mktCap",0),
        "Beta":      d.get("beta",0),
        "PERatio":   d.get("priceEarningsRatio"),
        "PBRatio":   d.get("priceToBookRatio"),
        "LastDiv":   d.get("lastDiv",0)
    } for d in j]

def fetch_history(sym):
    url = f"{BASE_URL}/historical-price-full/{sym}"
    j = requests.get(url, params={"apikey":FMP_KEY, "timeseries":HIST_DAYS}).json()
    return j.get("historical", [])

def compute_metrics_for_batch(df):
    year = str(datetime.datetime.utcnow().year)
    ma50, ma200, ytd = [], [], []
    for sym, price, last_div in zip(df.Symbol, df.Price, df.LastDiv):
        hist = fetch_history(sym)
        closes = [h["close"] for h in hist]
        ma50.append(sum(closes[:50])/50 if len(closes)>=50 else None)
        ma200.append(sum(closes[:200])/200 if len(closes)>=200 else None)
        yc = [c for h,c in zip(hist,closes) if h["date"].startswith(year)]
        if yc:
            y0 = yc[-1]
            ytd.append((closes[0]/y0)-1 if y0 else None)
        else:
            ytd.append(None)
    df["MA50"] = ma50
    df["MA200"] = ma200
    df["YTDChange"] = ytd
    df["DividendYield"] = df["LastDiv"].fillna(0)/df["Price"].replace({0:None})

def update_master():
    tickers = pd.read_csv("state/master_tickers.csv")["Symbol"].tolist()
    all_rows = []
    # process in 500-symbol chunks
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        prices  = fetch_prices(batch)
        profs   = fetch_profiles(batch)
        df_batch = pd.DataFrame(prices).merge(pd.DataFrame(profs),
                                              on="Symbol", how="left")
        compute_metrics_for_batch(df_batch)
        all_rows.append(df_batch)
        time.sleep(0.2)  # throttle under 300 calls/min

    # combine and persist
    df = pd.concat(all_rows, ignore_index=True)
    os.makedirs("state", exist_ok=True)
    df.to_csv("state/master_prices.csv", index=False)
    print(f"master_prices.csv: {len(df)} rows with all metrics")

if __name__=="__main__":
    update_master()

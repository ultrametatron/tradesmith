import os, datetime, requests, pandas as pd

FMP_KEY     = os.getenv("FMP_API_KEY")
BASE_URL    = "https://financialmodelingprep.com/api/v3"
STATE_DIR   = "/data/state"
MASTER_FILE = f"{STATE_DIR}/master_prices.csv"
TOP250_FILE = f"{STATE_DIR}/top250.csv"
LIVE_FILE   = f"{STATE_DIR}/top250_live.csv"

def fetch_prices(symbols):
    url = f"{BASE_URL}/quote/{','.join(symbols)}"
    resp = requests.get(url, params={"apikey":FMP_KEY}, timeout=10); resp.raise_for_status()
    now = datetime.datetime.utcnow()
    rows=[]
    for d in resp.json():
        price=d.get("price",0); prev=d.get("previousClose") or price
        rows.append({
            "Symbol":d["symbol"], "Price":price,
            "ChangePct":(price-prev)/prev if prev else 0,
            "Volume":d.get("volume",0),"Timestamp":now
        })
    return pd.DataFrame(rows)

def update_top250_live():
    df_master = pd.read_csv(MASTER_FILE)
    df_top    = pd.read_csv(TOP250_FILE)
    df_prices = fetch_prices(df_top.Symbol.astype(str).tolist())
    df_live   = df_master.merge(df_prices, on="Symbol", how="inner")
    os.makedirs(STATE_DIR, exist_ok=True)
    df_live.to_csv(LIVE_FILE, index=False)
    print(f"[update_top250_live] Wrote {len(df_live)} rows to {LIVE_FILE}")

if __name__=="__main__":
    update_top250_live()

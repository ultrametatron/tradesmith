# 📈 TradeSmith: AI-Driven Intraday Trading Platform

**Goal:** Transform the grind of monitoring every stock in the Wilshire 5000 into a hands‑off, intelligent engine—so you capture top opportunities and control risk without manual oversight.

**Mission:** Every trading day, automatically identify the best 250 names, apply AI‑guided weight tweaks, and refine our factor mix hourly to maximize risk‑adjusted returns.

---

**TradeSmith** combines real-time data, quantitative signals, LLM reasoning, and a lightweight RL module into a seamless intraday trading workflow. Think of it as your 24/7 analyst, constantly scanning the entire market, making sense of complex patterns, and adjusting itself as conditions change.

---

## 🌟 What It Does Today

1. **Every 15 Minutes:**  
   - Fetches live prices & volumes from FMP for all tickers.  
   - Merges them with yesterday’s master metrics (MA50, MA200, YTD, DivYield, etc.).  
   - Re-scores and identifies the Top 250 candidates.
2. **LLM-Driven Adjustments:**  
   - Builds a compact prompt (including time-of-day & volume-imbalance context).  
   - Uses OpenAI’s o4-mini to suggest precise portfolio weight tweaks.  
3. **Apply & Log:**  
   - Executes those tweaks (paper only) and logs P&L into an equity-curve CSV.  
4. **Hourly RL-Light Learning:**  
   - Every ~4 cycles, reviews recent risk-adjusted returns.  
   - Nudges factor weights with entropy (diversification) & turnover controls.  
5. **Automated Reports:**  
   - Sends a 250-word summary each morning.  
   - Delivers a 400-word CIO memo each Saturday.

---

## 🔧 Core Components

| Script                         | Role                                                       |
|--------------------------------|------------------------------------------------------------|
| **worker.py**                  | Orchestrates 15‑min cycles via APScheduler                  |
| **update_master_prices.py**    | Daily refresh of MA50/MA200, YTD returns, dividend yields   |
| **rl_light_throttled.py**      | Hourly policy-gradient weight updates with entropy/turnover |
| **run_daily_delivery.py**      | Generates and emails daily summary                         |
| **run_weekly_report.py**       | Generates and emails weekly CIO memo                       |

---

## 🔄 Data & Workflow

```mermaid
flowchart LR
  A[15-min FMP Price Fetch] --> B[Merge w/ master_metrics.csv]
  B --> C[Compute Composite Score & Top 250]
  C --> D[Build LLM Prompt (with context)]
  D --> E[o4-mini Adjustment Suggestions]
  E --> F[Apply Adjustments & Log Equity Curve]
  F --> G{RL-Light Update Cycle?}
  G -- Yes (every 4 cycles) --> H[RL-Light Weight Update]
  G -- No --> I[Skip RL Update]
  H --> I
  I --> J[Append to equity_curve.csv]
  J --> K[Back to Next 15-min Cycle]
  K --> B
  J --> L[Daily/Weekly Reporting Crons]
```

This flowchart reflects both the linear progression of an intraday cycle and the looping behavior of the RL-Light update and reporting.

---
## 🚀 Quickstart

1. **Install** dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure** env vars (Render or local):  
   `OPENAI_API_KEY`, `FMP_API_KEY`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `DELIVERY_EMAIL`
3. **Deploy** on Render using `render.yaml` (worker + three cron jobs).

---

## 🛣️ Roadmap (Next)

| Enhancement                 | Impact   | Confidence | Effort |
|-----------------------------|----------|------------|--------|
| Adaptive learning-rate      | Medium   | Medium     | Low    |
| EWMA reward smoothing       | Medium   | High       | Low    |
| Risk-aversion coefficient   | Medium   | High       | Low    |
| ε-Greedy exploration        | Low      | Low        | Low    |

---

> **Note:** This system is paper-trading only. For live deployment, integrate a brokerage API and conduct thorough compliance reviews.

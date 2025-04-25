# TradeSmith (Main Branch)

**TradeSmith** is an autonomous intraday trading agent that uses OpenAI's `o4-mini` model for trading logic, quantitative signal analysis, and local NLP sentiment processing to simulate realistic global portfolio management. It runs on Render with a Python backend and uses data from IEX Cloud and DistilBERT.

---

## 🔧 Features

- **Intraday Trading Simulation**: Evaluates and adjusts a simulated portfolio every 10 minutes.
- **Signal-Based Ranking**: Scores 5,000 stocks based on ten financial metrics and ranks the top 250.
- **Sentiment Integration**: Locally runs DistilBERT to score 10 headlines per ticker with minimal memory use.
- **OpenAI-Powered Decisions**: Uses `o4-mini` for trade instructions, constrained by IPS rules.
- **Daily + Weekly Reports**: Generates a 250-word daily CIO update and a 400-word weekly memo using `gpt-4.1-mini`.
- **Budget-Conscious**: Entire system runs on a Render Starter plan with predictable API costs.

---

## 📁 Folder Structure

```
tradesmith/
├─ state/              # Persistent data (portfolio, tickers, logs)
├─ prompts/            # Templates for daily/weekly prompt construction
├─ schemas/            # JSON function call schemas
├─ *.py                # Core code modules
├─ requirements.txt    # Python dependencies
├─ Dockerfile          # Container setup
└─ render.yaml         # Scheduled job configuration
```

---

## ⚙️ Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-username/tradesmith.git
cd tradesmith
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Data
Ensure the following files exist under `state/`:
- `holdings.csv` – starting with 100,000 CASH
- `master_tickers.csv` – list of up to 5,000 global tickers
- `metric_weights.json` – initial equal weights for 10 metrics

### 4. Environment Variables
On Render or locally, define:
- `OPENAI_API_KEY`
- `IEX_TOKEN`

### 5. Deploy to Render
All tasks (intraday run, daily report, weekly memo) are configured in `render.yaml`.

---

## 📊 IPS Targets

Trade decisions respect the following investment policy:
- **Target Return**: 12% annualized
- **Portfolio Beta**: ~0.80
- **Sharpe Ratio**: > 0.70
- **Sortino Ratio**: > 0.75
- **Sector Cap**: 25%
- **Turnover Cap**: Weekly % defined in `holdings.csv`
- **Cost Budget**: Weekly AUD budget defined in `holdings.csv`

---

## 📈 Reporting Outputs

- **Daily Report** (`state/daily_reports.csv`)
  - Summary of equity performance, trades, risks (~250 words)
- **Weekly Report** (`state/weekly_reports.csv`)
  - Strategic memo on signals, return profile, risks (~400 words)

---

## 🔮 Roadmap

- Add valuation model support
- Support real execution via broker API
- Integrate reinforcement learning from trade history
- Add optional ASX-only branch (coming soon)

---

## 📜 License

MIT License. Feel free to fork, use, or contribute.

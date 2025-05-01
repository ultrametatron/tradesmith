# TradeSmith: Modular Trading Intelligence Pipeline

**Overview**  
TradeSmith is a modular trading intelligence system designed to ingest market data, compute quantitative factors, prompt large language models (LLMs) for decisions, apply reinforcement learning (RL-light) adjustments, and generate daily reports. The project emphasizes scalability, traceability, and cost-effectiveness by integrating Google BigQuery, GitHub Actions, and OpenAI APIs.

---

## 🚀 Features

- **Data Ingestion**: Pull stock quotes, fundamentals, and ticker metadata from the FMP API  
- **Central Storage**: Use Google BigQuery as a queryable, structured warehouse for all raw and derived data  
- **Factor Computation**: Compute and score valuation, growth, quality, and technical signals per ticker  
- **LLM Decision Engine**: Prompt an OpenAI model (e.g. `o4-mini`) to suggest portfolio actions  
- **Reinforcement Feedback**: Adjust logic using post-hoc RL-light gradient approximations  
- **Daily Reporting**: Automatically generate and store summaries, performance stats, and metadata  

---

## 🧱 Architecture Overview

```
+-------------+       +-----------------+       +------------------+
|   FMP API   | --->  |  Ingestion Jobs  | --->  |  BigQuery Tables |
+-------------+       +-----------------+       +------------------+
                                                |
                                                v
                                  +----------------------+
                                  |  Factor Computation  |
                                  +----------------------+
                                                |
                                                v
                                     +-----------------+
                                     |   LLM Prompts   |
                                     +-----------------+
                                                |
                                                v
                                  +----------------------+
                                  |   RL Adjustments     |
                                  +----------------------+
                                                |
                                                v
                                      +---------------+
                                      |   Reporting   |
                                      +---------------+
```

---

## 📊 Current Status

### ✅ Completed  
- Phase 1A: Local Setup — Python venv, GCP credentials, service account auth  
- Phase 1B: Table Creation — BigQuery dataset/schema creation  

### ⚙️ In Progress  
- Phase 1C: ETL Ingestion (Airbyte) — Replace GitHub Action with connector-based pipeline  

---

## 🗂️ Datasets & Tables (BigQuery)

| Dataset            | Tables                               | Purpose                                  |
|--------------------|--------------------------------------|------------------------------------------|
| `raw_market`       | `symbols`, `quotes_intraday`, `fundamentals_daily` | Price and fundamental data       |
| `factor_engine`    | `factor_scores`, `candidate_list`     | Signal computation and ranking         |
| `prompt_logs`      | `prompts`, `prompt_responses`         | Inputs and outputs of LLM calls        |
| `decision_history` | `decisions`, `executions`             | Suggested and executed portfolio moves |
| `rl_light`         | `rl_updates`, `kpi_tracking`          | Feedback adjustments and metrics       |
| `job_runs`         | `job_runs`                            | CI logs and run metadata               |
| `daily_reports`    | `daily_report_logs`                   | Daily narrative summaries and metrics  |

---

## ⚡ Quick Start

### Prerequisites  
- Python 3.9+  
- BigQuery-enabled GCP project  
- Service account key (JSON)  
- GitHub repository with Actions or Airbyte  

### Local Setup  
```bash
python3 -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"
```

---

## 🛣️ Development Roadmap

| Phase | Module                  | Status       | Description                                              |
|-------|-------------------------|--------------|----------------------------------------------------------|
| 1A    | Local Setup             | ✅ Completed | Python venv, GCP credentials setup                       |
| 1B    | Table Creation          | ✅ Completed | BigQuery schema design and dataset creation              |
| 1C    | ETL Ingestion (Airbyte) | ⚙️ In Progress | Replace GitHub Actions with Airbyte syncs              |
| 2     | Factor Computation      | ⏭️ Planned   | Compute valuation, growth, technical factors in SQL      |
| 3     | LLM Prompting           | ⏭️ Planned   | Build and log prompts to o4-mini                         |
| 4     | Decision Logging        | ⏭️ Planned   | Store decisions & simulated executions                   |
| 5     | RL-Light Feedback       | ⏭️ Planned   | Update weights based on KPI signals                      |
| 6     | Reporting               | ⏭️ Planned   | End-of-day narrative & metrics into `daily_reports`      |

---

## ⚖️ License

MIT License

---

*Maintained by Mayank P. | Built with OpenAI, BigQuery, Airbyte, and FMP.*  
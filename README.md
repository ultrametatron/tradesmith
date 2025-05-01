TradeSmith

TradeSmith is a modular AI-assisted trading intelligence system that integrates real-time market data, financial factor modeling, LLM-based decision-making, reinforcement learning adjustments, and end-of-day reporting.

The goal is to build an end-to-end research and execution pipeline that remains fully traceable, efficient, and easily extensible. It’s designed for use by researchers, algorithmic traders, and AI-assisted portfolio builders who want to prototype novel decision pipelines using open tooling and cloud-native infrastructure.

⸻

🚀 Features
	•	Data Ingestion: Pull stock quotes, fundamentals, and ticker metadata from the FMP API
	•	Central Storage: Use Google BigQuery as a queryable, structured warehouse for all raw and derived data
	•	Factor Computation: Compute and score valuation, growth, quality, and technical signals per ticker
	•	LLM Decision Engine: Prompt an OpenAI model (e.g. o4-mini) to suggest portfolio actions
	•	Reinforcement Feedback: Adjust logic using post-hoc RL-light gradient approximations
	•	Daily Reporting: Automatically generate and store summaries, performance stats, and metadata

⸻

🧱 Architecture Overview

+-------------+       +-----------------+       +------------------+
|   FMP API   | --->  |  Ingestion Jobs  | --->  |  BigQuery Tables  |
+-------------+       +-----------------+       +------------------+
                                                  |
                                                  v
                                        +-------------------+
                                        |  Factor Computation|
                                        +-------------------+
                                                  |
                                                  v
                                          +---------------+
                                          |  LLM Prompts  |
                                          +---------------+
                                                  |
                                                  v
                                        +------------------+
                                        |  RL Adjustments  |
                                        +------------------+
                                                  |
                                                  v
                                           +-------------+
                                           |  Reporting   |
                                           +-------------+



⸻

📊 Current Status

✅ Completed
	•	Phase 1A: Local environment and credentials setup
	•	Phase 1B: BigQuery dataset and table creation
	•	Local + cloud authentication and service account setup

⚙️ In Progress
	•	Phase 1C: ETL ingestion via Airbyte (FMP → BigQuery)
	•	Phase 2: Factor computation via SQL in BigQuery
	•	Phase 3: Prompt creation and LLM interaction
	•	Phase 4: Decision and execution tracking
	•	Phase 5: RL update loop and KPI tracking
	•	Phase 6: Daily narrative report generation
	•	ETL migration to Airbyte (replacing GitHub Actions ingestion)

⸻

🗂️ Datasets & Tables (BigQuery)

Dataset	Tables	Purpose
raw_market	symbols, quotes_intraday, fundamentals_daily	Price and financial data
factor_engine	factor_scores, candidate_list	Signal computation and ranking
prompt_logs	prompts, prompt_responses	Inputs and outputs of LLM calls
decision_history	decisions, executions	Suggested and executed portfolio moves
rl_light	rl_updates, kpi_tracking	Feedback adjustment and performance logs
job_runs	job_runs	CI logs, Git hashes, status markers
daily_reports	daily_report_logs	EOD text summary and JSON metrics



⸻

⚡ Quick Start

Prerequisites
	•	Python 3.9+
	•	BigQuery-enabled GCP project
	•	Service account key (JSON)
	•	GitHub repository with Actions enabled

Local Setup

python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account.json"



⸻

🛣️ Development Roadmap

✅ Completed & In Progress

Phase	🧩 Module	Status	Description
1A	Local Setup	✅ Completed	Python venv, GCP credentials, service account auth
1B	Table Creation	✅ Completed	BigQuery schema design and dataset creation
1C	ETL Ingestion (Airbyte)	⚙️ In Progress	Replace GitHub Action with connector-based pipeline

⏭️ Planned

Phase	🧩 Module	Description
2	Factor Computation	BigQuery SQL: quality, value, growth, technical metrics
3	LLM Prompting	Generate prompts using enriched data + call o4-mini
4	Decision Logging	Capture actions, confidence scores, simulated fills
5	RL-Light Feedback	Adjust factor weights based on reward signals
6	Reporting	Generate daily summaries with stats + LLM commentary

✅ Completed

Phase	🧩 Module	Description
1A	Local Setup	Python venv, GCP credentials, service account auth
1B	Table Creation	BigQuery schema design and dataset creation

⚙️ In Progress

Phase	🧩 Module	Description
1C	ETL Ingestion (Airbyte)	Replace GitHub Action with connector-based pipeline

⏭️ Planned

Phase	🧩 Module	Description
2	Factor Computation	BigQuery SQL: quality, value, growth, technical metrics
3	LLM Prompting	Generate prompts using enriched data + call o4-mini
4	Decision Logging	Capture actions, confidence scores, simulated fills
5	RL-Light Feedback	Adjust factor weights based on reward signals
6	Reporting	Generate daily summaries with stats + LLM commentary


⸻

⚖️ License

MIT License

⸻

Repository maintained by Mayank P. | Built with OpenAI, BigQuery, GitHub Actions, and FMP.
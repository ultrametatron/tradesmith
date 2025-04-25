"""
Generate weekly 400-word CIO memo every Friday at 20:00 UTC.
"""
import datetime, pandas as pd
from log_kpis import metrics
from call_tradesmith import ask_report

def main():
    today = datetime.date.today()
    kpi = metrics()
    tr = pd.read_csv("state/commissions_log.csv", parse_dates=["Timestamp"])
    week_num = today.isocalendar()[1]
    weekly_trades = tr[tr.Timestamp.dt.isocalendar().week == week_num]

    tpl = open("prompts/weekly_report.txt").read()
    prompt = tpl.replace("${report_date}", str(today)) \
                .replace("${weekly_kpis}", str(kpi)) \
                .replace("${weekly_trades}", weekly_trades.to_csv(index=False))

    memo = ask_report(prompt)
    with open("state/weekly_reports.csv", "a") as f:
        f.write(f"{today},{memo.replace(',', ' ')}\n")

if __name__ == "__main__":
    main()

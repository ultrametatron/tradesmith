"""
Generate daily 250-word CIO report at 20:00 UTC.
"""
import datetime, pandas as pd
from call_tradesmith import ask_report

def main():
    today = datetime.date.today()
    eq = pd.read_csv("state/equity_log.csv", names=["date","value"],
                     parse_dates=["date"]).tail(10)
    tr = pd.read_csv("state/commissions_log.csv", parse_dates=["Timestamp"])
    today_tr = tr[tr.Timestamp.dt.date == today]

    tpl = open("prompts/daily_report.txt").read()
    prompt = tpl.replace("${report_date}", str(today)) \
                .replace("${equity_table}", eq.to_csv(index=False)) \
                .replace("${trades_table}", today_tr.to_csv(index=False))

    report = ask_report(prompt)
    with open("state/daily_reports.csv", "a") as f:
        f.write(f"{today},{report.replace(',', ';')}\n")

if __name__ == "__main__":
    main()

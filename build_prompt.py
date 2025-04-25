"""
Build the daily prompt with current candidates and IPS caps.
"""
from string import Template

def build_daily(df):
    tpl = Template(open("prompts/daily_prompt.txt").read())
    return tpl.substitute(
        table=df.to_csv(index=False),
        weekly_cap=df.Weekly_Cap.iloc[0],
        weekly_budget=df.Weekly_Cost_Budget.iloc[0]
    )

# call_tradesmith.py

import os
import json
import openai

# load your API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# models
MODEL_TRADES = "o4-mini"
MODEL_REPORT = "gpt-4.1-mini"

# load the function‐call schema JSON directly
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "adjustments.json")
with open(_SCHEMA_PATH, "r") as f:
    adjustments_schema = json.load(f)

def ask_trades(prompt: str) -> dict:
    """
    Call o4-mini to get trade adjustments.
    Returns the parsed JSON arguments from the function call.
    """
    resp = openai.ChatCompletion.create(
        model=MODEL_TRADES,
        messages=[{"role": "system", "content": prompt}],
        functions=[adjustments_schema],
        function_call="process_adjustments",
        temperature=0
    )
    # extract the JSON arguments returned by the function call
    return json.loads(resp.choices[0].message.function_call.arguments)

def ask_report(prompt: str) -> str:
    """
    Call gpt-4.1-mini to get a narrative report.
    Returns the assistant’s content.
    """
    resp = openai.ChatCompletion.create(
        model=MODEL_REPORT,
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content

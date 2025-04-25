import os
import json
from openai import OpenAI

# instantiate the new client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# load your function-call schema JSON directly
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "adjustments.json")
with open(_SCHEMA_PATH, "r") as f:
    adjustments_schema = json.load(f)

# model names
MODEL_TRADES = "o4-mini"
MODEL_REPORT = "gpt-4.1-mini"

def ask_trades(prompt: str) -> dict:
    """
    Use the new v1 client to call the trades function.
    Returns the parsed JSON arguments.
    """
    resp = client.chat.completions.create(
        model=MODEL_TRADES,
        messages=[{"role": "system", "content": prompt}],
        functions=[adjustments_schema],
        function_call="process_adjustments",
        temperature=0
    )
    # extract the function_call arguments
    fc = resp.choices[0].message.function_call
    return json.loads(fc.arguments)

def ask_report(prompt: str) -> str:
    """
    Use the new v1 client to generate narrative reports.
    Returns the assistant’s reply content.
    """
    resp = client.chat.completions.create(
        model=MODEL_REPORT,
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content

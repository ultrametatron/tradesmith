import os
import json
from openai import OpenAI

# Instantiate the new client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the function-call schema JSON directly
_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__),
    "schemas",
    "adjustments.json"
)
with open(_SCHEMA_PATH, "r") as f:
    adjustments_schema = json.load(f)

MODEL_TRADES = "o4-mini"
MODEL_REPORT = "gpt-4.1-mini"

def ask_trades(prompt: str) -> dict:
    """
    Call o4-mini to get trade adjustments via the 'process_adjustments' function.
    """
    resp = client.chat.completions.create(
        model=MODEL_TRADES,
        messages=[{"role": "system", "content": prompt}],
        tools=[
            {
                "type": "function",
                "function": adjustments_schema
            }
        ],
        tool_choice={
            "type": "function",
            "function": {"name": adjustments_schema["name"]}
        },
        temperature=0
    )
    fc = resp.choices[0].message.function_call
    return json.loads(fc.arguments)


def ask_report(prompt: str) -> str:
    """
    Call gpt-4.1-mini to get a narrative report.
    """
    resp = client.chat.completions.create(
        model=MODEL_REPORT,
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content

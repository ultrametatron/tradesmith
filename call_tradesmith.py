"""
Wrap OpenAI calls for trade adjustments and narrative reports.
"""
import openai, os, json, importlib

schema = importlib.import_module("schemas.adjustments").__dict__

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_TRADES = "o4-mini"
MODEL_REPORT = "gpt-4.1-mini"

def ask_trades(prompt: str) -> dict:
    """Call o4-mini to get trade JSON."""
    resp = openai.ChatCompletion.create(
        model=MODEL_TRADES,
        messages=[{"role": "system", "content": prompt}],
        functions=[schema],
        function_call="process_adjustments",
        temperature=0
    )
    return json.loads(resp.choices[0].message.function_call.arguments)

def ask_report(prompt: str) -> str:
    """Call GPT-4.1-mini to get narrative."""
    resp = openai.ChatCompletion.create(
        model=MODEL_REPORT,
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content

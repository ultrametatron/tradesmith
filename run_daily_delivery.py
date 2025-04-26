#!/usr/bin/env python
import os
import smtplib
from email.message import EmailMessage
import pandas as pd
from call_tradesmith import ask_report

# ── Configuration ────────────────────────────────────────────────────────────────
STATE_DIR      = "/data/state"
EQUITY_CURVE   = os.path.join(STATE_DIR, "equity_curve.csv")
SMTP_SERVER    = os.getenv("SMTP_SERVER")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.getenv("SMTP_USER")
SMTP_PASS      = os.getenv("SMTP_PASS")
DELIVERY_EMAIL = os.getenv("DELIVERY_EMAIL")
# ────────────────────────────────────────────────────────────────────────────────

def generate_report_text() -> str:
    """Use your existing prompt/report logic (250 words)."""
    # Example: you might build a prompt elsewhere; here we just call into ask_report()
    prompt = (
        "Generate a concise 250-word portfolio summary for the equity curve data."
    )
    return ask_report(prompt)

def send_email(report_text: str):
    """Compose and send an email with the report and the CSV attached."""
    # Read the CSV
    with open(EQUITY_CURVE, "rb") as f:
        csv_data = f.read()

    msg = EmailMessage()
    msg["Subject"] = "Daily Portfolio Report + Equity Curve"
    msg["From"] = SMTP_USER
    msg["To"] = DELIVERY_EMAIL

    # Plain-text body (report_text)
    msg.set_content(report_text)

    # Attach the CSV
    msg.add_attachment(
        csv_data,
        maintype="text",
        subtype="csv",
        filename="equity_curve.csv"
    )

    # Send
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

def main():
    # 1) Generate the narrative report
    report = generate_report_text()

    # 2) Send the email with CSV attached
    send_email(report)
    print(f"✅ Sent daily report to {DELIVERY_EMAIL}")

if __name__ == "__main__":
    main()

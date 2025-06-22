# run_report.py
import os
import requests

# Get secrets from Railway's environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DOMAINS_STR = os.getenv("DOMAINS_TO_CHECK")

def check_domain(domain: str) -> str:
    """Checks a single domain and returns a status string."""
    url = f"https://check.skiddle.id/?domain={domain}&json=true"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if domain in data and "blocked" in data[domain]:
            status = "🔴 Blocked" if data[domain]["blocked"] else "🟢 Not Blocked"
            return f"{domain}: {status}"
        return f"{domain}: ⚠️ Invalid API response"
    except Exception as e:
        print(f"ERROR checking {domain}: {e}")
        return f"{domain}: ⚠️ Request Failed"

def send_telegram_message(text: str):
    """Sends a message directly to the Telegram API."""
    print("Preparing to send Telegram message...")
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except Exception as e:
        print(f"FATAL: Failed to send Telegram message: {e}")
        print(f"Response from Telegram: {response.text if 'response' in locals() else 'N/A'}")

# --- Main script logic ---
if __name__ == "__main__":
    print("--- Cron job script started. ---")
    if not all([BOT_TOKEN, CHAT_ID, DOMAINS_STR]):
        error_msg = "FATAL: One or more environment variables (TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, DOMAINS_TO_CHECK) are missing."
        print(error_msg)
        # We can't send a Telegram message if the token/ID is missing, so we just exit.
        exit()

    domains = [domain.strip() for domain in DOMAINS_STR.split(',')]
    report_lines = ["*Domain Status Report*"]

    for domain in domains:
        if domain:
            status = check_domain(domain)
            report_lines.append(status)

    final_report = "\n".join(report_lines)
    send_telegram_message(final_report)
    print("--- Cron job script finished. ---")

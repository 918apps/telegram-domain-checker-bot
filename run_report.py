# run_report.py
import os
import requests
import logging
from telegram import Bot
import asyncio

# Set up logging to see output in Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get secrets from Railway's environment variables
TOKEN = os.getenv("7082647057:AAF_6jilIW0CyrgANUvbbH_k79HH9C7mm_w")
ADMIN_CHAT_ID = os.getenv("5330994420")
DOMAINS_TO_CHECK = os.getenv("odin55thor.com, modalnekat.online, pewe128jk.space, pewe128lk.store, pewe128ui.space")

def check_single_domain(domain: str) -> str:
    """Checks a single domain and returns a status string."""
    url = f"https://check.skiddle.id/?domain={domain}&json=true"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if domain in data:
            blocked = data[domain].get("blocked", False)
            status_text = "🔴 Blocked" if blocked else "🟢 Not Blocked"
            return f"{domain}: {status_text}"
        else:
            return f"{domain}: ⚠️ Domain not found."
    except Exception as e:
        logger.error(f"Error checking {domain}: {e}")
        return f"{domain}: ⚠️ Error fetching data."

async def main():
    """The main function that will be run by the cron job."""
    logger.info("--- Cron Job Started: Running domain report ---")
    
    if not TOKEN or not ADMIN_CHAT_ID or not DOMAINS_TO_CHECK:
        logger.error("Missing one or more required environment variables. Exiting.")
        return

    bot = Bot(token=TOKEN)
    domains = [domain.strip() for domain in DOMAINS_TO_CHECK.split(',')]
    report_lines = [" Domain Status Report:"]
    
    for domain in domains:
        if domain:
            status = check_single_domain(domain) # Note: this is not async
            report_lines.append(status)
            
    final_report = "\n".join(report_lines)
    
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=final_report)
    logger.info(f"Report sent successfully to Chat ID {ADMIN_CHAT_ID}.")

if __name__ == "__main__":
    asyncio.run(main())

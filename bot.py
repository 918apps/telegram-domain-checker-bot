# bot.py
import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging so we can see what's happening in Railway
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CORRECTLY GET SECRETS FROM RAILWAY VARIABLES ---
# This looks for the VARIABLE NAME in Railway.
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DOMAINS_TO_CHECK = os.getenv("DOMAINS_TO_CHECK")

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Replies when /start is sent."""
    await update.message.reply_text("Hello! I am online and the scheduler is running.")

# --- CORE LOGIC ---

def check_single_domain(domain: str) -> str:
    """Checks one domain and returns a status string."""
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
            return f"{domain}: ⚠️ Domain not found in API response."
    except Exception as e:
        logger.error(f"Error checking {domain}: {e}")
        return f"{domain}: ⚠️ Error fetching data."

async def run_scheduled_check(application: Application):
    """This is the function that runs every 30 minutes."""
    logger.info("--- Scheduler triggered: Running domain check... ---")
    
    if not ADMIN_CHAT_ID or not DOMAINS_TO_CHECK:
        logger.warning("ADMIN_CHAT_ID or DOMAINS_TO_CHECK is not set. Skipping scheduled report.")
        return

    domains = [domain.strip() for domain in DOMAINS_TO_CHECK.split(',')]
    report_lines = [" Domain Status Report:"]
    
    for domain in domains:
        if domain:
            status = check_single_domain(domain)
            report_lines.append(status)
            
    final_report = "\n".join(report_lines)
    
    try:
await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=final_report)
logger.info(f"Scheduled report sent successfully to Chat ID {ADMIN_CHAT_ID}.")
    except Exception as e:
        logger.error(f"Failed to send scheduled report: {e}")

# --- MAIN SETUP ---

def main():
    """Starts the bot and the scheduler."""
    if not TOKEN:
        logger.critical("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_scheduled_check, 'interval', minutes=30, kwargs={'application': application})
    
    logger.info("Bot and scheduler have started successfully.")
    
    application.run_polling()

if __name__ == "__main__":
    main()

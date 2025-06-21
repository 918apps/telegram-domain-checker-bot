import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get secrets from environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DOMAINS_TO_CHECK = os.getenv("DOMAINS_TO_CHECK")

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text("Hello! I am a domain status checker bot.\n\nUse /check <domain> for a single check.\nUse /getid to find your Chat ID for setting up hourly reports.")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns the user's chat ID."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your Chat ID is: `{chat_id}`")

async def check_domain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually checks a single domain."""
    if not context.args:
        await update.message.reply_text("Usage: /check <domain>")
        return
    
    domain = context.args[0]
    status = await check_single_domain(domain)
    await update.message.reply_text(status)

# --- Core Logic & Scheduled Task ---

async def check_single_domain(domain: str) -> str:
    """Checks a single domain and returns a status string."""
    url = f"https://check.skiddle.id/?domain={domain}&json=true"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()
        if domain in data:
            blocked = data[domain].get("blocked", False)
            status_text = "🔴 Blocked" if blocked else "🟢 Not Blocked"
            return f"{domain}: {status_text}"
        else:
            return f"{domain}: ⚠️ Domain not found in API response."
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {domain}: {e}")
        return f"{domain}: ⚠️ Error fetching data."
    except Exception as e:
        logger.error(f"An unexpected error occurred for {domain}: {e}")
        return f"{domain}: ⚠️ An unexpected error occurred."

async def run_hourly_check(context: ContextTypes.DEFAULT_TYPE):
    """The function that runs every hour, checks all domains, and sends a report."""
    logger.info("Running hourly domain check...")
    
    if not ADMIN_CHAT_ID or not DOMAINS_TO_CHECK:
        logger.warning("ADMIN_CHAT_ID or DOMAINS_TO_CHECK not set. Skipping hourly check.")
        return

    domains = [domain.strip() for domain in DOMAINS_TO_CHECK.split(',')]
    report_lines = [" hourly domain status report:"]
    
    for domain in domains:
        if domain: # Ensure we don't process empty strings
            status = await check_single_domain(domain)
            report_lines.append(status)
            
    final_report = "\n".join(report_lines)
    
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=final_report)
        logger.info("Hourly report sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send hourly report to {ADMIN_CHAT_ID}: {e}")

# --- Main Application Setup ---

def main():
    """Start the bot and the scheduler."""
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getid", get_id))
    application.add_handler(CommandHandler("check", check_domain_command))

    # Create and start the scheduler
    scheduler = AsyncIOScheduler()
    # Schedule the job to run every hour
    scheduler.add_job(run_hourly_check, 'interval', minutes=30, context=application)
    scheduler.start()
    
    logger.info("Bot and scheduler started successfully!")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()

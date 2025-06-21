import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging to see what the bot is doing
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get secrets from Railway's environment variables
TOKEN = os.getenv("7082647057:AAF_6jilIW0CyrgANUvbbH_k79HH9C7mm_w")
ADMIN_CHAT_ID = os.getenv("5330994420")
DOMAINS_TO_CHECK = os.getenv("nos138crm.store, nos138bj.space, nos138bg.store, venom55.net, venom55.com, venom55.live, venom55.club")

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """A simple start command to confirm the bot is online."""
    await update.message.reply_text("Hello! I am online. Use /reportnow to get an instant report.")

async def check_domain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually checks a single domain."""
    if not context.args:
        await update.message.reply_text("Usage: /check <domain.com>")
        return
    
    domain = context.args[0]
    status = await check_single_domain(domain)
    await update.message.reply_text(status)

async def force_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """NEW: Forces an immediate check and sends the report."""
    # Check if the person sending the command is the admin
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("Sorry, only the admin can run this command.")
        return

    await update.message.reply_text("On it! Generating and sending the report now...")
    await run_scheduled_check(context) # We just reuse the existing report function

# --- Core Logic & Scheduled Task ---

async def check_single_domain(domain: str) -> str:
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
            return f"{domain}: ⚠️ Domain not found in API response."
    except Exception as e:
        logger.error(f"Error checking {domain}: {e}")
        return f"{domain}: ⚠️ Error fetching data."

async def run_scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    """This function runs on a schedule OR when called by /reportnow."""
    logger.info("--- Running domain check task ---")
    
    if not ADMIN_CHAT_ID or not DOMAINS_TO_CHECK:
        logger.warning("ADMIN_CHAT_ID or DOMAINS_TO_CHECK is not set. Skipping check.")
        return

    domains = [domain.strip() for domain in DOMAINS_TO_CHECK.split(',')]
    report_lines = [" Domain Status Report:"]
    
    for domain in domains:
        if domain:
            status = await check_single_domain(domain)
            report_lines.append(status)
            
    final_report = "\n".join(report_lines)
    
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=final_report)
        logger.info(f"Report sent successfully to Chat ID {ADMIN_CHAT_ID}.")
    except Exception as e:
        logger.error(f"Failed to send report to {ADMIN_CHAT_ID}: {e}")

# --- Main Application Setup ---

def main():
    """Start the bot and the scheduler."""
    application = Application.builder().token(TOKEN).build()

    # Register all our command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_domain_command))
    application.add_handler(CommandHandler("reportnow", force_report)) # <-- NEW HANDLER

    # Create and start the scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_scheduled_check, 'interval', minutes=30, context=application)
    scheduler.start()
    
    logger.info("Bot and scheduler started successfully.")
    
    application.run_polling()

if __name__ == "__main__":
    main()

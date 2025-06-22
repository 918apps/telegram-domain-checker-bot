# bot.py - The Interactive Trigger Bot
import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Get Secrets from Railway Variables ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Replies when the /start command is sent."""
    logger.info("Received /start command.")
    await update.message.reply_text("Hello! I am the interactive bot. Send /checknow to get an instant report.")

async def checknow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the reporting script via a webhook."""
    logger.info("Received /checknow command.")

    # 1. Check if the user is authorized
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        logger.warning(f"Unauthorized user {update.effective_chat.id} tried to run /checknow.")
        await update.message.reply_text("Sorry, you are not authorized to use this command.")
        return

    # 2. Check if the webhook URL is configured
    if not WEBHOOK_URL:
        logger.error("FATAL: WEBHOOK_URL environment variable is not set!")
        await update.message.reply_text("Error: The report webhook URL is not configured on my end.")
        return
        
    await update.message.reply_text("On it! Triggering the report job now...")
    
    # 3. Try to call the webhook
    try:
        logger.info(f"Calling webhook: {WEBHOOK_URL}")
        response = requests.post(WEBHOOK_URL)
        response.raise_for_status()  # This will raise an error for 4xx or 5xx responses
        logger.info("Webhook triggered successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to trigger webhook. Error: {e}")
        await update.message.reply_text("Error: There was a problem triggering the report job.")

# --- Main Application Setup ---

def main():
    """Starts the interactive bot."""
    if not TOKEN:
        logger.critical("FATAL ERROR: TELEGRAM_BOT_TOKEN is not set. The bot cannot start.")
        return
        
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("checknow", checknow_command))
    
    logger.info("Interactive bot started successfully. Listening for commands...")
    application.run_polling()

if __name__ == "__main__":
    main()

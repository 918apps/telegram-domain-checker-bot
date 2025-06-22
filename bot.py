# bot.py - The Interactive Trigger
import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get secrets from Railway variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # This will be the URL to trigger our cron job
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Replies when the /start command is sent."""
    await update.message.reply_text("Hello! I am the interactive bot. Send /checknow to get an instant report.")

async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers the reporting script via a webhook."""
    # First, check if the person sending the command is the admin
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this command.")
        return

    await update.message.reply_text("On it! Triggering the report now...")
    logger.info("Received /checknow command. Triggering webhook.")
    
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL is not set!")
        await update.message.reply_text("Error: The webhook URL is not configured.")
        return
        
    try:
        # This sends a request to the special URL to run our cron job script
        response = requests.post(WEBHOOK_URL)
        response.raise_for_status()
        logger.info("Webhook triggered successfully.")
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}")
        await update.message.reply_text("Error: Could not trigger the report job.")

def main():
    """Starts the interactive bot."""
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("checknow", check_now))
    
    logger.info("Interactive bot started and listening for commands...")
    application.run_polling()

if __name__ == "__main__":
    main()

import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Use /check <domain> to check if a domain is blocked.")

async def check_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /check <domain>")
        return
    domain = context.args[0]
    url = f"https://check.skiddle.id/?domain={domain}&json=true"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if domain in data:
                blocked = data[domain]["blocked"]
                status = "Blocked" if blocked else "Not Blocked"
                await update.message.reply_text(f"{domain}: {status}")
            else:
                await update.message.reply_text("Error: Domain not found in response.")
        else:
            await update.message.reply_text("Error: Failed to fetch data.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_domain))
    application.run_polling()

if __name__ == "__main__":
    main()

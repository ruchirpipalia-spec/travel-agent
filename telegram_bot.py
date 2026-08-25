import os
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from dotenv import load_dotenv
from agent import chat, memory
from memory import get_memory_summary
from alerts import run_checks

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"User: {user_message}")

    await update.message.chat.send_action("typing")

    response = chat(user_message)
    print(f"Agent: {response}")

    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memory_summary = get_memory_summary(memory)

    if memory_summary:
        welcome = f"✈️ Welcome back! Here's what I remember:\n\n{memory_summary}\n\nWhat can I help you with?"
    else:
        welcome = "✈️ Hi! I'm your personal travel agent. I can search flights and hotels, track prices, and alert you when fares drop.\n\nTry asking me something like:\n- 'Find flights to Dublin in March'\n- 'Watch SFO to Tokyo under $900'\n- 'What hotels in Paris for next week?'"

    await update.message.reply_text(welcome)

async def scheduled_price_check(app):
    """Runs price checks every 24 hours in the background."""
    while True:
        print(f"⏰ Running scheduled price check at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        try:
            run_checks()
        except Exception as e:
            print(f"❌ Price check error: {e}")
        # Wait 24 hours
        await asyncio.sleep(24 * 60 * 60)

async def post_init(app):
    """Start the background scheduler when the bot starts."""
    asyncio.create_task(scheduled_price_check(app))
    print("✅ Price check scheduler started — runs every 24 hours")

def main():
    print("🤖 Telegram bot starting...")

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running. Open Telegram and message your bot!")
    app.run_polling()

if __name__ == "__main__":
    main()
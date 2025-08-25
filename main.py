import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# Logger
logging.basicConfig(level=logging.INFO)

# Supabase info from Render environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Telegram bot token from Render env
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Channel ID to monitor
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003056692685"))

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post or update.message
    if message and message.chat_id == CHANNEL_ID:
        title = message.text or ""
        # Use first 200 chars as summary
        summary = title[:200] if len(title) > 200 else title

        # Insert into Supabase
        data = {"title": title, "summary": summary}
        response = supabase.table("movies").insert(data).execute()
        logging.info(f"Inserted: {data}, response: {response}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Watch channel messages
    app.add_handler(MessageHandler(filters.ALL & filters.Chat(CHANNEL_ID), handle_new_message))

    logging.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()

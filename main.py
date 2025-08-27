import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from supabase import create_client, Client

# -------------------
# Flask Web Server
# -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# -------------------
# Supabase Setup
# -------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------
# Telegram Bot Setup
# -------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1003056692685   # آیدی کانال خودت

async def handle_channel_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        message = update.channel_post
        title = message.text or ""
        summary = message.caption or ""

        # ذخیره در Supabase
        data = {
            "title": title,
            "summary": summary
        }
        supabase.table("movies").insert(data).execute()
        print(f"Inserted: {data}")

app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(MessageHandler(filters.ALL & filters.ChatType.CHANNEL, handle_channel_messages))

# -------------------
# Run Flask + Bot
# -------------------
if __name__ == "__main__":
    def run_bot():
        asyncio.run(app_telegram.run_polling())

    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

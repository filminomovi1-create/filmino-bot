import os
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from supabase import create_client, Client

# -------------------
# Flask App (برای اینکه Render/Railway زنده نگه داره)
# -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# -------------------
# Supabase Config
# -------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------
# Telegram Bot Config
# -------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def handle_channel_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        message = update.channel_post

        # عنوان و توضیحات (متن / کپشن)
        title = message.caption or message.text or ""
        summary = message.text or ""

        # اطلاعات فایل (در صورتی که فایل باشد)
        file_id = None
        if message.video:
            file_id = message.video.file_id
        elif message.document:
            file_id = message.document.file_id
        elif message.photo:
            file_id = message.photo[-1].file_id  # بزرگترین سایز

        # آماده سازی داده‌ها
        data = {
            "title": title,
            "summary": summary,
            "file_id": file_id,
            "message_id": message.message_id,
            "chat_id": message.chat.id
        }

        # درج در Supabase
        supabase.table("movies").insert(data).execute()
        print(f"Inserted: {data}")

# -------------------
# Bot Init
# -------------------
app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(
    MessageHandler(filters.ALL & filters.ChatType.CHANNEL, handle_channel_messages)
)

# -------------------
# اجرای همزمان Flask + Bot
# -------------------
if __name__ == "__main__":
    import asyncio
    import threading

    # اجرای ربات تلگرام در یک Thread جدا
    def run_bot():
        asyncio.run(app_telegram.run_polling())

    threading.Thread(target=run_bot).start()

    # اجرای سرور Flask
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

import os
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from supabase import create_client

# دریافت متغیرهای محیطی از Render
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# اتصال به Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == CHANNEL_ID:
        # فقط فیلم‌ها را پردازش می‌کنیم
        if update.message.video:
            title = update.message.caption or "No Caption"
            summary = f"Video ID: {update.message.video.file_id}"  # می‌توانی خلاصه دلخواه بسازی
            # اضافه کردن به Supabase
            data = {"title": title, "summary": summary}
            supabase.table("movies").insert(data).execute()

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    # ساخت و اجرای ربات تلگرام
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # اجرای همزمان ربات و وب‌سرور
    import asyncio
    async def main():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    
    asyncio.run(main())

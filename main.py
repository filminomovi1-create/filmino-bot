import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# دریافت متغیرها از محیط Render
BOT_TOKEN = os.environ["BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])  # ایدی کانال با منفی

# ساخت کلاینت Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بررسی اینکه پیام از کانال مورد نظر آمده باشد
    if update.effective_chat.id != CHANNEL_ID:
        return

    message = update.effective_message
    title = None
    summary = None

    # اگر پیام حاوی ویدیو/فیلم باشد
    if message.video:
        title = message.caption or "بدون عنوان"
        summary = f"Video ID: {message.video.file_id}"

    # اگر پیام حاوی متن بود (مثلاً خلاصه)
    elif message.text:
        title = message.text[:100]  # 100 کاراکتر اول به عنوان عنوان
        summary = message.text

    # اضافه کردن به جدول Supabase
    if title and summary:
        data = {"title": title, "summary": summary}
        try:
            supabase.table("movies").insert(data).execute()
            print(f"Added to Supabase: {data}")
        except Exception as e:
            print(f"Supabase Error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_channel_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

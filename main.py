import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# گرفتن اطلاعات حساس از Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

# اتصال به Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بررسی اینکه پیام از چنل ماست
    if update.effective_chat.id != CHANNEL_ID:
        return
    
    message = update.message

    # متن اصلی پیام
    text = message.text or ""
    
    # اگر پیام شامل فایل است (فیلم، ویدئو، سند)، caption را هم بگیریم
    caption = message.caption or ""
    
    # ترکیب متن و کپشن
    content = text.strip() + " " + caption.strip()
    content = content.strip()  # حذف فاصله اضافی

    if not content:
        return

    # اضافه کردن به Supabase
    data = {"name": content}
    supabase.table("movies").insert(data).execute()
    print(f"Added movie: {content}")

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # همه پیام‌ها رو چک می‌کنیم
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, new_message))
    
    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from supabase import create_client, Client

# -----------------------------
# تنظیمات اولیه
# -----------------------------
TOKEN = os.getenv("BOT_TOKEN")  # توی Render به عنوان Environment Variable بذار
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

WEBHOOK_URL = "https://filmino-bot.onrender.com/webhook"

# اتصال به Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# هندلرها
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کاربر /start بزنه"""
    await update.message.reply_text("سلام 👋 من ربات فلیمینو هستم!")

async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی پستی توی کانال بیاد"""
    if update.channel_post.video:
        caption = update.channel_post.caption or "بدون عنوان"
        file_id = update.channel_post.video.file_id

        # ذخیره در سوپابیس
        try:
            supabase.table("films").insert({
                "title": caption,
                "file_id": file_id
            }).execute()
            logger.info(f"فیلم ذخیره شد: {caption}")
        except Exception as e:
            logger.error(f"خطا در ذخیره به Supabase: {e}")

# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI()
application = Application.builder().token(TOKEN).build()

# اضافه کردن هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, channel_post))

@app.on_event("startup")
async def on_startup():
    """موقع بالا اومدن سرور"""
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set on {WEBHOOK_URL}")

@app.post("/webhook")
async def webhook(req: Request):
    """دریافت پیام از تلگرام"""
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@app.get("/")
async def home():
    return {"status": "ok"}

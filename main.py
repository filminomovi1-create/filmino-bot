# main.py
import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from supabase import create_client
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Env vars (در Render باید ست شوند) ===
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # ex: https://your-app.onrender.com/webhook
SET_WEBHOOK_ON_START = os.environ.get("SET_WEBHOOK_ON_START", "true").lower() in ("1","true","yes")

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set in env")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logger.error("Supabase vars missing")

# Supabase client (service role — use only on server)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Telegram Bot + Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

app = Flask(__name__)

def extract_title(caption):
    if not caption:
        return None
    return caption.strip().splitlines()[0][:200]

def build_message_link(chat_id, username, message_id):
    if username:
        return f"https://t.me/{username}/{message_id}"
    cid = str(chat_id)
    if cid.startswith("-100"):
        cid = cid[4:]
    return f"https://t.me/c/{cid}/{message_id}"

def channel_post_handler(update, context):
    # این تابع برای پیام‌های کانال اجرا می‌شود
    msg = update.channel_post
    if msg is None:
        return

    kind = None
    file_id = None
    file_unique_id = None
    duration = None
    width = None
    height = None

    if msg.video:
        kind = "video"
        file_id = msg.video.file_id
        file_unique_id = msg.video.file_unique_id
        duration = msg.video.duration
        width = msg.video.width
        height = msg.video.height
    elif msg.document:
        kind = "document"
        file_id = msg.document.file_id
        file_unique_id = msg.document.file_unique_id
    elif msg.audio:
        kind = "audio"
        file_id = msg.audio.file_id
        file_unique_id = msg.audio.file_unique_id
        duration = msg.audio.duration
    elif msg.animation:
        kind = "animation"
        file_id = msg.animation.file_id
        file_unique_id = msg.animation.file_unique_id
    elif msg.photo:
        kind = "photo"
        ph = msg.photo[-1]
        file_id = ph.file_id
        file_unique_id = ph.file_unique_id
    else:
        # متن یا نوع پشتیبانی نشده — فعلاً رد می‌کنیم
        return

    caption = msg.caption or ""
    title = extract_title(caption)
    channel_username = msg.chat.username  # بدون @
    chat_id = msg.chat.id
    message_id = msg.message_id
    message_link = build_message_link(chat_id, channel_username, message_id)

    row = {
        "chat_id": chat_id,
        "channel_username": ("@" + channel_username) if channel_username else None,
        "message_id": message_id,
        "title": title,
        "caption": caption,
        "file_type": kind,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "duration": duration,
        "width": width,
        "height": height,
        "message_link": message_link,
    }

    try:
        supabase.table("channel_media").upsert(row, on_conflict=["chat_id","message_id"]).execute()
        logger.info("Upserted message %s from chat %s", message_id, chat_id)
    except Exception as e:
        logger.exception("Failed to upsert to Supabase: %s", e)

# ثبت Handler در Dispatcher
dispatcher.add_handler(MessageHandler(Filters.chat_type.channel, channel_post_handler))

# روت‌های وب
@app.route("/", methods=["GET"])
def index():
    return "OK - bot webhook app", 200

@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        dispatcher.process_update(update)
    except Exception as e:
        logger.exception("Error processing update: %s", e)
        return "error", 500
    return "ok", 200

# البته می‌تونیم وبهوک را روی استارت ست کنیم
def set_webhook_if_needed():
    if WEBHOOK_URL and SET_WEBHOOK_ON_START:
        try:
            logger.info("Setting webhook to %s", WEBHOOK_URL)
            # حذف وبهوک قبلی
            bot.delete_webhook()
            res = bot.set_webhook(WEBHOOK_URL)
            logger.info("setWebhook result: %s", res)
        except Exception as e:
            logger.exception("Failed to set webhook: %s", e)

if __name__ == "__main__":
    # فقط در حالت محلی برای تست - ولی روی Render gunicorn اجرا می‌کند
    set_webhook_if_needed()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

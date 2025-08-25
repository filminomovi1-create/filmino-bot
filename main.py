# app.py
import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Env vars (ست‌شون کن توی Render) ===
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
# WEBHOOK_URL را در Render ست کن: https://<your-app>.onrender.com/webhook
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# === تنظیمات بوت و Supabase ===
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)

# === کمک کننده‌ها ===
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

# === هندلرها ===
def start_handler(update, context):
    chat = update.effective_chat
    try:
        context.bot.send_message(chat_id=chat.id, text="سلام! من ربات فیلم شما هستم ✅")
    except Exception as e:
        logger.exception("failed to reply in start_handler: %s", e)

def channel_post_handler(update, context):
    # توی webhook این آپدیت در update.channel_post قرار می‌گیره
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
        # متن خالص یا چیزِ پشتیبانی نشده — فعلاً رد کن
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

# ثبت هندلرها در دیسپچر
dispatcher.add_handler(MessageHandler(Filters.chat_type.channel, channel_post_handler))
dispatcher.add_handler(MessageHandler(Filters.chat_type.private, start_handler))

# === روت‌ها ===
@app.route("/", methods=["GET"])
def index():
    return "OK - render bot", 200

@app.route("/healthz", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_json = request.get_json(force=True)
        update = Update.de_json(update_json, bot)
        dispatcher.process_update(update)
    except Exception as e:
        logger.exception("Error processing update: %s", e)
        return "error", 500
    return "ok", 200

# === ست‌کردن وبهوک خودکار (اگر WEBHOOK_URL ست شده باشد) ===
if WEBHOOK_URL:
    try:
        # حذف وبهوک قبلی (اختیاری) و ست وبهوک جدید
        bot.delete_webhook()
        bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook set to %s", WEBHOOK_URL)
    except Exception as e:
        logger.exception("Failed to set webhook: %s", e)

# app متغیر مورد نیاز برای gunicorn: gunicorn app:app -b 0.0.0.0:$PORT

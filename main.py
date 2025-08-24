import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from supabase import create_client

# ENV VARS: حتما در Railway/Render ست کن
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def extract_title(caption: str | None) -> str | None:
    if not caption:
        return None
    # خط اول کپشن را به عنوان عنوان فیلم برمی‌داریم
    return caption.strip().splitlines()[0][:200]

def build_message_link(chat_id: int, username: str | None, message_id: int) -> str:
    # اگر کانال public است:
    if username:
        return f"https://t.me/{username}/{message_id}"
    # اگر کانال private است:
    # فرمت: https://t.me/c/<chat_id_without_-100>/<message_id>
    cid = str(chat_id)
    if cid.startswith("-100"):
        cid = cid[4:]
    return f"https://t.me/c/{cid}/{message_id}"

async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = msg.chat

    # نوع فایل و مشخصات
    kind, file_id, file_unique_id = None, None, None
    duration = width = height = None

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
        # اگر متن خالی/غیرمدیا بود، فعلاً رد کن
        return

    caption = msg.caption or ""
    title = extract_title(caption)

    channel_username = chat.username  # بدون @
    chat_id = chat.id
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

    # upsert بر اساس chat_id+message_id تا تکراری نشود
    supabase.table("channel_media").upsert(row, on_conflict=["chat_id","message_id"]).execute()

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Bot is alive ✅")

if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # پیام‌های کانال
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, on_channel_post))
    # تست دستی در pv گروه/چت شخصی
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, ping))

    # فقط برای کانال‌ها کافیست:
    app.run_polling(allowed_updates=["channel_post", "message"])

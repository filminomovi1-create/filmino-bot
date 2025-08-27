import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
from supabase import create_client, Client

# === تنظیمات محیطی ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# === اتصال به سوپابیس ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === اپ Flask ===
app = Flask(__name__)

# === هندلر /start ===
async def start(update: Update, context):
    user = update.effective_user
    user_id = user.id
    username = user.username or "بدون نام"

    # ذخیره کاربر در سوپابیس
    supabase.table("users").insert({
        "user_id": user_id,
        "username": username
    }).execute()

    await update.message.reply_text(f"سلام {username}! 🎉 شما ثبت شدید.")

# === راه‌اندازی بات ===
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

# === وبهوک برای رندر ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
def home():
    return "Bot is running on Render ✅"

# === اجرای برنامه روی Render ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook"
    )
    app.run(host="0.0.0.0", port=port)

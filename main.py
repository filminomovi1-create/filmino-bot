import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ----------------------------
# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# مقداردهی Flask و ربات تلگرام
app = Flask(__name__)
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # توکن تلگرام رو از Render environment variables بگیر
bot = Bot(TOKEN)

# ----------------------------
# مسیر تست وب‌سرور
@app.route("/")
def home():
    return "Bot is running on Render 🚀"

# ----------------------------
# Webhook برای تلگرام (اختیاری، اگر میخوای از polling استفاده نکنی)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # می‌تونی دستورات اینجا اضافه کنی
    return "ok"

# ----------------------------
# فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات شما آنلاین است 🚀")

# ----------------------------
# اجرای ربات با polling
def run_bot():
    app_logger = logging.getLogger("telegram.bot")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # polling (Render برای webhook هم قابل تنظیم است)
    application.run_polling()

# ----------------------------
if __name__ == "__main__":
    from threading import Thread

    # اجرای ربات در یک ترد جداگانه
    Thread(target=run_bot).start()

    # اجرای وب‌سرور
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

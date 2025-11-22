#!/usr/bin/env python3
"""
Minimal Telegram webhook bot using python-telegram-bot v13 + Flask.

Usage:
- Set environment variables:
    BOT_TOKEN      -> your bot token (always keep secret)
    WEBHOOK_PATH   -> e.g. /telegram-webhook
    PUBLIC_URL     -> e.g. https://your-service.onrender.com  (optional; if present the app will call setWebhook)
    FLASK_DEBUG    -> "true" or "1" to enable debug mode (optional)
- Start: python app.py
"""
import os
import logging
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Read env vars ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN غير موجود في متغيرات البيئة. اضبطه قبل التشغيل.")

WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "/telegram-webhook")
PUBLIC_URL = os.environ.get("PUBLIC_URL")  # e.g. https://ceiling-report-bot.onrender.com
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

# Optional: admins list (comma-separated user ids)
ADMINS = set()
admins_env = os.environ.get("ADMINS", "")
for a in [x.strip() for x in admins_env.split(",") if x.strip()]:
    try:
        ADMINS.add(int(a))
    except ValueError:
        pass

app = Flask(__name__)

# --- Bot & Dispatcher setup ---
bot = Bot(token=BOT_TOKEN)
# Dispatcher(bot, update_queue, workers, use_context)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)


# --- Handlers ---
def start(update, context):
    user = update.effective_user
    name = user.first_name if user else "مستخدم"
    text = f"مرحباً {name}!\nأرسل /help لرؤية الأوامر."
    update.message.reply_text(text)


def help_cmd(update, context):
    text = (
        "أوامر البوت:\n"
        "/start - بداية\n"
        "/help - هذه المساعدة\n"
        "/verify - تحقق (مثال)\n"
        "/status - تعرض حالة بسيطة\n"
        "/admin_panel - لوحة إدارة (لمسجّلين فقط)\n"
    )
    update.message.reply_text(text)


def verify(update, context):
    # مثال تحقق بسيط
    update.message.reply_text("تم التحقق بنجاح ✅")


def status(update, context):
    update.message.reply_text("الحالة: التطبيق يعمل بشكل طبيعي.")


def admin_panel(update, context):
    user = update.effective_user
    if user and user.id in ADMINS:
        update.message.reply_text("Welcome to admin panel. (مكان لتنفيذ أوامر الإدارة)")
    else:
        update.message.reply_text("ليس لديك صلاحية الوصول إلى لوحة الإدارة.")


def error_handler(update, context):
    logger.exception("Exception while handling an update: %s", context.error)


# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_cmd))
dispatcher.add_handler(CommandHandler("verify", verify))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("admin_panel", admin_panel))

dispatcher.add_error_handler(error_handler)


# --- Flask routes ---
@app.route("/", methods=["GET"])
def root():
    return "OK - bot server", 200


@app.route(WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, bot)
            dispatcher.process_update(update)
        except Exception:
            logger.exception("Failed to process update")
            # Return 200 to Telegram to avoid repeated retries, unless you want to surface errors.
            return "error", 200
        return "ok", 200
    else:
        abort(405)


# --- Helper to set webhook automatically if PUBLIC_URL is given ---
def set_webhook_if_needed():
    if not PUBLIC_URL:
        logger.info("PUBLIC_URL not set — skipping automatic setWebhook.")
        return

    webhook_url = PUBLIC_URL.rstrip("/") + WEBHOOK_PATH
    current = bot.get_webhook_info()
    current_url = current.url if current else None
    if current_url == webhook_url:
        logger.info("Webhook already set to %s", webhook_url)
        return

    logger.info("Setting webhook to %s", webhook_url)
    ok = bot.set_webhook(url=webhook_url)
    if not ok:
        logger.warning("setWebhook returned False — check Telegram response and logs.")
    else:
        logger.info("setWebhook OK.")


# --- Run app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Try to set webhook on start if PUBLIC_URL provided
    try:
        set_webhook_if_needed()
    except Exception:
        logger.exception("Failed to set webhook automatically. You can set it manually with Telegram API.")

    logger.info("Starting Flask app on 0.0.0.0:%s, webhook path: %s", port, WEBHOOK_PATH)
    app.run(host="0.0.0.0", port=port, debug=FLASK_DEBUG)

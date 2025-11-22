import os
from telegram.ext import Updater, CommandHandler
from flask import Flask, request
import telegram

# Fetch environment variables set on Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL_PATH = os.environ.get('WEBHOOK_URL_PATH')
PORT = os.environ.get('PORT', 8000)

app = Flask(__name__)

# --- تعريف وظائف البوت (Telegram Functions) ---
def start(update, context):
    # رسالة الترحيب التي ستظهر عند إرسال /start
    update.message.reply_text("👋 أهلاً بك! أنا روبوت تقارير السقف. أرسل لي /status لمعرفة حالة الربط.")

# --- تهيئة البوت (Initialization) ---
def setup_updater():
    # Get updater and dispatcher
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add command handlers
    dp.add_handler(CommandHandler("start", start))
    
    # Configure Webhook listening for Render
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=WEBHOOK_URL_PATH)
    
    print("Bot updater initialized and listening.")
    return updater

# Initialize the bot updater once
if BOT_TOKEN:
    updater = setup_updater()
else:
    print("FATAL ERROR: BOT_TOKEN is not set.")

# --- مسارات الويب (Flask Webhooks) ---
@app.route('/', methods=['GET'])
def home():
    # Health check endpoint for Render
    return "Telegram Bot Webhook Receiver is running.", 200

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    # Process the update sent by Telegram
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), updater.bot)
        updater.dispatcher.process_update(update)
    return 'ok', 200

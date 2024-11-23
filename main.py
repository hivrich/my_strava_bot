import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Telegram Bot Token и Webhook URL
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TOKEN)

# Обработчик команды /start
def start(update, context):
    auth_url = os.getenv("STRAVA_AUTH_URL", "https://example.com/auth")  # Укажи свою ссылку
    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Нажмите кнопку ниже, чтобы авторизоваться в Strava:", reply_markup=reply_markup)

# Настройка диспетчера
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))

# Маршрут для Telegram вебхука
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error"}), 500

# Тестовый маршрут
@app.route("/test", methods=["GET"])
def test():
    return "Бот работает!", 200

# Основной запуск приложения
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8080))
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)

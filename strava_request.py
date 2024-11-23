import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler
from config import TELEGRAM_TOKEN, WEBHOOK_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Обработчик команды /start
def start(update, context):
    try:
        auth_url = "https://www.strava.com/oauth/authorize?client_id=137731&response_type=code&redirect_uri=https://mystravabot-production.up.railway.app/callback&scope=read,activity:read_all"
        keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Нажмите кнопку ниже, чтобы авторизоваться в Strava:", reply_markup=reply_markup)
        logger.info("Команда /start успешно обработана")
    except Exception as e:
        logger.error(f"Ошибка обработки команды /start: {e}")

# Настройка диспетчера
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))

# Маршрут для Telegram вебхука
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
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
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=8080)

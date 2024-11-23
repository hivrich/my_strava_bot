import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Чтение переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
PORT = int(os.getenv("PORT", 5000))

# Проверка переменных окружения
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не задан. Установите переменную окружения TELEGRAM_TOKEN.")
    exit(1)
if not WEBHOOK_URL:
    logger.error("WEBHOOK_URL не задан. Установите переменную окружения WEBHOOK_URL.")
    exit(1)
if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
    logger.error("STRAVA_CLIENT_ID или STRAVA_CLIENT_SECRET не заданы.")
    exit(1)

# Инициализация Flask-приложения
app = Flask(__name__)

# Инициализация Telegram Bot API
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Команда /start получена от пользователя: {update.effective_user.id}")
    await update.message.reply_text("Привет! Бот работает!")

# Регистрация обработчика команды /start
application.add_handler(CommandHandler("start", start))

# Маршрут для обработки вебхуков Telegram
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    logging.info(f"Webhook получил данные: {data}")
    if data:
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    return jsonify({"status": "ok"})

# Маршрут для обработки обратного вызова от Strava
@app.route("/strava_callback", methods=["GET"])
def strava_callback():
    code = request.args.get('code')
    if code:
        response = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': STRAVA_CLIENT_ID,
                'client_secret': STRAVA_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        if response.status_code == 200:
            return "Авторизация успешна. Вы можете вернуться в Telegram."
        else:
            return "Ошибка при авторизации в Strava."
    return "Код авторизации не предоставлен."

# Главная точка запуска приложения
if __name__ == "__main__":
    # Устанавливаем вебхук
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    # Запускаем Flask-приложение
    app.run(host="0.0.0.0", port=PORT)

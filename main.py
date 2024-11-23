import os
import logging
from flask import Flask, request, jsonify
from urllib.parse import quote as url_quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получен запрос на /start: {update}")
    try:
        auth_url = f"https://www.strava.com/oauth/authorize?client_id={os.getenv('STRAVA_CLIENT_ID')}&redirect_uri={url_quote(os.getenv('WEBHOOK_URL'))}&response_type=code&scope=read,activity:read_all"
        keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы авторизоваться в Strava:",
            reply_markup=reply_markup
        )
        logger.info("Ответ на /start отправлен")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")

# Главная функция для запуска бота
def main():
    # Загрузка переменных окружения
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", 8443))

    if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
        raise ValueError("TELEGRAM_BOT_TOKEN или WEBHOOK_URL не установлены")

    logger.info(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
    logger.info(f"PORT: {PORT}")

    # Инициализация Telegram бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Запуск бота
    logger.info("Настройка вебхука...")
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")

    # Flask-эндпоинт для проверки
    @app.route("/test", methods=["GET"])
    def test():
        return jsonify({"status": "ok", "message": "Сервер работает"})

    # Обработка Telegram вебхуков через Flask
    @app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
    def webhook():
        json_data = request.get_json()
        logger.info(f"Получен вебхук: {json_data}")
        application.update_queue.put(json_data)
        return jsonify({"status": "ok"})

    # Запуск Flask приложения
    logger.info("Запуск Flask-приложения...")
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

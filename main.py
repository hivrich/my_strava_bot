import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Flask-приложение
app = Flask(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# Создаем Telegram-приложение
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Хендлер для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получен запрос на /start от {update.effective_user.id}")
    auth_url = "https://example.com/auth"  # Заменить на реальный URL авторизации Strava
    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нажмите кнопку ниже, чтобы авторизоваться в Strava:", reply_markup=reply_markup)

# Добавляем хендлер команды /start
application.add_handler(CommandHandler("start", start))

# Обработка запросов от Telegram (вебхук)
@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    try:
        json_update = request.get_json()
        update = Update.de_json(json_update, application.bot)
        application.update_queue.put_nowait(update)
        logger.info(f"Обработан запрос: {json_update}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Тестовый маршрут для проверки сервера
@app.route("/test", methods=["GET", "POST"])
def test_endpoint():
    logger.info(f"Получен запрос на /test: {request.data}")
    return jsonify({"status": "ok", "message": "Test successful!"}), 200

# Запуск приложения
if __name__ == "__main__":
    logger.info("Запуск приложения...")

    # Запуск Telegram Webhook с использованием coroutines
    async def run_bot():
        await application.initialize()
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
        await application.start()
        logger.info("Telegram бот запущен.")

    import asyncio
    asyncio.run(run_bot())

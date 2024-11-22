import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from strava_auth import get_authorization_url, exchange_code_for_token, refresh_access_token
from strava_request import get_athlete_activities, get_activity_photos, get_athlete_info
import sqlite3

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Инициализация базы данных
def init_db():
    logger.info("Initializing database")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, access_token TEXT, refresh_token TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS likes
                 (user_id INTEGER, activity_id TEXT, PRIMARY KEY (user_id, activity_id))''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/start received from user {update.effective_user.id}")
    await update.message.reply_text("Привет! Я ваш Strava бот. Используйте /help для списка доступных команд.")

# Основная функция запуска
def main() -> None:
    try:
        # Загрузка переменных окружения
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        PORT = int(os.getenv("PORT", "8080"))

        if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
            raise ValueError("TELEGRAM_BOT_TOKEN or WEBHOOK_URL not set in environment variables.")

        # Инициализация базы данных
        init_db()

        # Создание приложения Telegram
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start))

        # Запуск вебхука
        logger.info(f"Starting webhook on {WEBHOOK_URL}:{PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
        )

    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == '__main__':
    main()

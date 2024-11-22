import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"/start command received from user {update.effective_user.id}")
        auth_url = "https://example.com/auth"  # Заменить на реальный URL авторизации Strava
        keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Нажмите кнопку ниже, чтобы авторизоваться в Strava:', reply_markup=reply_markup)
        logger.info("Response to /start sent successfully.")
    except Exception as e:
        logger.error(f"Error in /start handler: {e}")

# Функция для команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"/help command received from user {update.effective_user.id}")
        await update.message.reply_text(
            "Вот что я могу:\n"
            "/start - Начать общение\n"
            "/help - Показать справку\n"
            "/activities - Показать последние активности (в разработке)"
        )
    except Exception as e:
        logger.error(f"Error in /help handler: {e}")

# Обработчик неизвестных команд
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.warning(f"Received unknown command: {update.message.text}")
        await update.message.reply_text("Извините, я не понимаю эту команду.")
    except Exception as e:
        logger.error(f"Error in unknown command handler: {e}")

# Обработчик для получения данных активностей
async def get_activities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"/activities command received from user {update.effective_user.id}")
        await update.message.reply_text("Эта функция пока в разработке.")
    except Exception as e:
        logger.error(f"Error in /activities handler: {e}")

# Основная функция запуска
def main() -> None:
    try:
        # Загрузка переменных окружения
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        PORT = int(os.getenv("PORT", "8080"))

        # Логирование переменных окружения для проверки
        logger.info(f"TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}")
        logger.info(f"WEBHOOK_URL={WEBHOOK_URL}")
        logger.info(f"PORT={PORT}")

        if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
            raise ValueError("TELEGRAM_BOT_TOKEN or WEBHOOK_URL not set in environment variables.")

        # Инициализация базы данных
        init_db()

        # Создание приложения Telegram
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("activities", get_activities))
        application.add_handler(MessageHandler(filters.COMMAND, unknown))

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

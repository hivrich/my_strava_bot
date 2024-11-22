import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработка необработанных ошибок
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"/start command received from user {update.effective_user.id}")
        auth_url = "https://example.com/auth"  # Здесь можно вставить ссылку на авторизацию Strava
        keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Нажмите кнопку ниже, чтобы авторизоваться в Strava:', reply_markup=reply_markup)
        logger.info("Response to /start sent successfully.")
    except Exception as e:
        logger.error(f"Error in /start handler: {e}")

# Основная функция запуска
def main():
    try:
        # Проверяем и логируем все переменные окружения
        logger.info(f"Все доступные переменные окружения: {dict(os.environ)}")

        # Загрузка переменных окружения
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        PORT = int(os.getenv("PORT", "8080"))

        # Проверяем наличие необходимых переменных
        logger.info(f"TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}")
        logger.info(f"WEBHOOK_URL={WEBHOOK_URL}")
        logger.info(f"PORT={PORT}")

        if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
            raise ValueError("TELEGRAM_BOT_TOKEN or WEBHOOK_URL not set in environment variables.")

        # Создание приложения Telegram
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
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

if __name__ == "__main__":
    main()

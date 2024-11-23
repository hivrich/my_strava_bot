import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Команда /start от {update.effective_user.id}")
    await update.message.reply_text("Привет! Я бот для работы со Strava.")

# Основной запуск приложения
def main():
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", "8443"))

    if not TELEGRAM_BOT_TOKEN or not WEBHOOK_URL:
        logger.error("Переменные окружения TELEGRAM_BOT_TOKEN или WEBHOOK_URL не установлены.")
        raise ValueError("TELEGRAM_BOT_TOKEN или WEBHOOK_URL отсутствуют.")

    # Создание приложения Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Запуск вебхука
    logger.info(f"Запуск вебхука на {WEBHOOK_URL}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()

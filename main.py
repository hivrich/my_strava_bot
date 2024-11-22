import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработка необработанных ошибок
def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Функция для команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получен запрос на /start: {update}")
    try:
        auth_url = "https://example.com/auth"  # Заменить на реальную ссылку Strava
        keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            'Нажмите кнопку ниже, чтобы авторизоваться в Strava:',
            reply_markup=reply_markup
        )
        logger.info("Ответ на /start отправлен")
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}")

# Простой обработчик POST-запросов для теста
class TestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            logger.info(f"Получен POST-запрос: {post_data.decode('utf-8')}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            self.send_response(500)
            self.end_headers()

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

        # Логируем запуск вебхука
        logger.info("Попытка запуска вебхука...")
        logger.info(f"URL вебхука: {WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")

        # Запуск вебхука
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
        )

        # Дополнительно запускаем тестовый сервер для логирования запросов
        logger.info(f"Запуск тестового сервера на порту {PORT}")
        server = HTTPServer(('', PORT), TestHandler)
        server.serve_forever()

    except Exception as e:
        logger.error(f"Ошибка в main: {e}")

if __name__ == "__main__":
    logger.info("Запуск бота...")
    main()

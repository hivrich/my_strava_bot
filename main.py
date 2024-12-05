import os
import logging
from quart import Quart, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
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

# Инициализация Quart-приложения
app = Quart(__name__)

# Инициализация Telegram Bot API
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Команда /start получена от пользователя: {update.effective_user.id}")
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&response_type=code&redirect_uri={WEBHOOK_URL}/strava_callback&scope=read,activity:read_all"
    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нажмите на кнопку ниже, чтобы авторизоваться в Strava:", reply_markup=reply_markup)
    logging.info("Ответ на команду /start отправлен пользователю.")

# Регистрация обработчика команды /start
application.add_handler(CommandHandler("start", start))

# Асинхронный маршрут для обработки вебхуков Telegram
@app.post("/webhook")
async def telegram_webhook():
    data = await request.get_json()
    logging.info(f"Webhook получил данные: {data}")
    if data:
        update = Update.de_json(data, application.bot)
        await application.initialize()  # Инициализация приложения перед обработкой обновлений
        await application.process_update(update)
    return jsonify({"status": "ok"})

# Асинхронный маршрут для обработки обратного вызова от Strava
@app.get("/strava_callback")
async def strava_callback():
    code = request.args.get('code')
    state = request.args.get('state')  # Получаем state для идентификации Telegram ID
    if code and state:
        try:
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
                data = response.json()
                telegram_id = state
                logger.info(f"Успешная авторизация в Strava для Telegram ID: {telegram_id}")
                # Отправляем сообщение в Telegram
                await application.bot.send_message(
                    chat_id=telegram_id,
                    text="Вы успешно авторизовались в Strava! 🎉"
                )
                return "Авторизация прошла успешно. Вернитесь в Telegram!"
            else:
                logger.error(f"Ошибка авторизации в Strava: {response.text}")
                return "Ошибка при авторизации в Strava."
        except Exception as e:
            logger.error(f"Ошибка обработки Strava callback: {e}")
            return "Произошла ошибка при обработке вашего запроса."
    logger.warning("Код авторизации не предоставлен или ошибка state.")
    return "Код авторизации не предоставлен или ошибка state."

# Главная точка запуска приложения
if __name__ == "__main__":
    # Устанавливаем вебхук
    asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
    # Запускаем Quart-приложение
    app.run(host="0.0.0.0", port=PORT)

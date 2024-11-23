import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)

# Получение переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
PORT = int(os.getenv("PORT", 5000))

# Проверка наличия необходимых переменных окружения
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не задан. Установите переменную окружения TELEGRAM_TOKEN.")
    exit(1)

if not WEBHOOK_URL:
    logger.error("WEBHOOK_URL не задан. Установите переменную окружения WEBHOOK_URL.")
    exit(1)

if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
    logger.error("STRAVA_CLIENT_ID или STRAVA_CLIENT_SECRET не заданы.")
    exit(1)

# Инициализация приложения Telegram Bot
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Генерация URL для авторизации в Strava
    auth_url = (
        f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}"
        f"&redirect_uri={WEBHOOK_URL}/strava_callback&response_type=code&scope=read"
        f"&state={user_id}"
    )
    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Нажмите кнопку ниже, чтобы авторизоваться в Strava:",
        reply_markup=reply_markup
    )

# Регистрация обработчика команды /start
application.add_handler(CommandHandler("start", start))

# Маршрут для обработки вебхука Telegram
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data:
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    return jsonify({"status": "ok"})

# Маршрут для обработки обратного вызова от Strava
@app.route("/strava_callback", methods=["GET"])
def strava_callback():
    code = request.args.get('code')
    state = request.args.get('state')  # Получаем user_id из параметра state
    if code and state:
        # Обмен кода на токен доступа
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
            access_token = data['access_token']
            refresh_token = data['refresh_token']
            expires_at = data['expires_at']
            # Здесь вы можете сохранить токены для пользователя с user_id (state)
            # Например, сохранить их в базе данных
            return "Авторизация успешна. Можете вернуться в Telegram."
        else:
            return "Ошибка при получении токена от Strava."
    else:
        return "Код авторизации или state не предоставлены."

if __name__ == "__main__":
    # Устанавливаем вебхук при запуске приложения
    application.bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    # Запускаем Flask-приложение
    app.run(host="0.0.0.0", port=PORT)

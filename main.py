import os
import logging
from quart import Quart, request, jsonify, redirect
from telegram import Bot
import requests
import urllib.parse
import uuid

# Настройки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
PORT = int(os.getenv("PORT", 5000))

bot = Bot(token=TELEGRAM_TOKEN)
app = Quart(__name__)

# Хранилище временных данных (state)
state_storage = {}

# Генерация ссылки для авторизации Strava
@app.route("/start", methods=["GET"])
async def start():
    telegram_id = request.args.get("telegram_id")
    if not telegram_id:
        return "Telegram ID не предоставлен.", 400

    # Создаем уникальный state
    state = str(uuid.uuid4())
    state_storage[state] = telegram_id

    # Формируем ссылку для авторизации
    params = {
        "client_id": STRAVA_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": f"{WEBHOOK_URL}/strava_callback",
        "scope": "read,activity:read_all",
        "state": state
    }
    auth_url = f"https://www.strava.com/oauth/authorize?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

# Callback для обработки авторизации Strava
@app.route("/strava_callback", methods=["GET"])
async def strava_callback():
    code = request.args.get("code")
    state = request.args.get("state")

    # Проверяем state
    if not state or state not in state_storage:
        return "Код авторизации не предоставлен или ошибка state.", 400

    telegram_id = state_storage.pop(state)

    # Обрабатываем код авторизации
    if code:
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code"
            }
        )
        if response.status_code == 200:
            bot.send_message(chat_id=telegram_id, text="Вы успешно авторизовались в Strava! 🎉")
            return "Авторизация прошла успешно. Вернитесь в Telegram!"
        else:
            bot.send_message(chat_id=telegram_id, text="Ошибка авторизации в Strava. Попробуйте снова.")
            return "Ошибка при авторизации в Strava.", 400
    else:
        bot.send_message(chat_id=telegram_id, text="Ошибка авторизации в Strava. Код авторизации не предоставлен.")
        return "Код авторизации не предоставлен.", 400

# Главная точка запуска приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

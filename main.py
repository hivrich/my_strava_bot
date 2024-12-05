import os
import logging
import uuid
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

# Временное хранилище для state (в реальном проекте лучше использовать базу данных)
state_storage = {}

# Получение данных пользователя Strava
def get_strava_athlete_data(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    if response.status_code == 200:
        return response.json()  # Возвращаем данные пользователя
    else:
        logger.error(f"Ошибка получения данных Strava: {response.text}")
        return None

# Получение активностей пользователя Strava
def get_strava_activities(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers)
    if response.status_code == 200:
        return response.json()  # Возвращаем список активностей
    else:
        logger.error(f"Ошибка получения активностей Strava: {response.text}")
        return []

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = str(uuid.uuid4())  # Генерируем уникальный state
    state_storage[user_id] = state  # Сохраняем state для пользователя

    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={STRAVA_CLIENT_ID}"
        f"&redirect_uri={WEBHOOK_URL}/strava_callback"
        f"&response_type=code"
        f"&scope=read,activity:read,activity:read_all,profile:read_all"
        f"&state={state}"
    )

    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нажмите кнопку ниже, чтобы авторизоваться в Strava:", reply_markup=reply_markup)

# Регистрация обработчика команды /start
application.add_handler(CommandHandler("start", start))

# Асинхронный маршрут для обработки вебхуков Telegram
@app.post("/webhook")
async def telegram_webhook():
    data = await request.get_json()
    if data:
        update = Update.de_json(data, application.bot)
        await application.initialize()
        await application.process_update(update)
    return jsonify({"status": "ok"})

# Асинхронный маршрут для обработки обратного вызова от Strava
@app.route("/strava_callback", methods=["GET"])
async def strava_callback():
    code = request.args.get("code")
    returned_state = request.args.get("state")
    user_id = None

    # Проверяем соответствие state
    for uid, saved_state in state_storage.items():
        if saved_state == returned_state:
            user_id = uid
            break

    if not user_id:
        return "Ошибка: state не совпадает или пользователь не найден.", 400

    # Обмениваем code на access token
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
    )

    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]

        # Получаем данные пользователя
        athlete_data = get_strava_athlete_data(access_token)

        if athlete_data:
            athlete_name = f"{athlete_data['firstname']} {athlete_data['lastname']}"
            await application.bot.send_message(
                chat_id=user_id,
                text=f"Вы успешно авторизовались в Strava! \ud83c\udf89\nВаш профиль: {athlete_name}",
            )

            # Получаем активности пользователя
            activities = get_strava_activities(access_token)
            photos_found = False

            for activity in activities:
                if "photos" in activity and activity["photos"]:
                    for photo in activity["photos"]:
                        if "urls" in photo and "1800" in photo["urls"]:
                            photos_found = True
                            photo_url = photo["urls"]["1800"]
                            await application.bot.send_photo(chat_id=user_id, photo=photo_url)

            if not photos_found:
                await application.bot.send_message(
                    chat_id=user_id,
                    text="Фотографии в ваших активностях не найдены.",
                )
        else:
            await application.bot.send_message(
                chat_id=user_id,
                text="Ошибка получения данных пользователя Strava. Попробуйте позже.",
            )
        return "Авторизация прошла успешно. Вернитесь в Telegram!"
    else:
        return "Ошибка при авторизации в Strava.", 400

# Главная точка запуска приложения
if __name__ == "__main__":
    asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
    app.run(host="0.0.0.0", port=PORT)

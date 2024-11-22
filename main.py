import os
import logging
import sys
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from strava_auth import get_authorization_url, exchange_code_for_token, refresh_access_token
from strava_request import get_athlete_activities, get_activity_photos, get_athlete_info
import sqlite3

# Загрузка переменных окружения из .env
load_dotenv()

# Получение переменных из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8080"))

# Проверка, что переменные загружены
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set. Check your .env file.")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is not set. Check your .env file.")

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

# Сохранение токенов пользователя
def save_user_tokens(user_id, access_token, refresh_token):
    logger.info(f"Saving tokens for user {user_id}")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, access_token, refresh_token) VALUES (?, ?, ?)",
              (user_id, access_token, refresh_token))
    conn.commit()
    conn.close()
    logger.info(f"Tokens saved for user {user_id}")

# Получение токенов пользователя
def get_user_tokens(user_id):
    logger.info(f"Getting tokens for user {user_id}")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT access_token, refresh_token FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    logger.info(f"Tokens retrieved for user {user_id}: {'Found' if result else 'Not found'}")
    return result if result else (None, None)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Start command received from user {update.effective_user.id}")
    auth_url = get_authorization_url()
    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Нажмите кнопку ниже, чтобы авторизоваться в Strava:', reply_markup=reply_markup)
    logger.info(f"Start command processed for user {update.effective_user.id}")

async def auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Auth callback received")
    query = update.callback_query
    code = query.data
    user_id = query.from_user.id

    logger.info(f"Exchanging code for token for user {user_id}")
    access_token, refresh_token = exchange_code_for_token(code)
    if access_token and refresh_token:
        save_user_tokens(user_id, access_token, refresh_token)
        await query.answer()
        await query.edit_message_text(text="Вы успешно авторизовались в Strava!")
        logger.info(f"User {user_id} successfully authorized")
    else:
        await query.answer()
        await query.edit_message_text(text="Произошла ошибка при авторизации. Попробуйте еще раз.")
        logger.error(f"Authorization failed for user {user_id}")

async def show_activities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Show activities command received from user {update.effective_user.id}")
    user_id = update.effective_user.id
    access_token, refresh_token = get_user_tokens(user_id)

    if not access_token:
        await update.message.reply_text("Пожалуйста, сначала авторизуйтесь в Strava.")
        logger.info(f"User {user_id} not authorized")
        return

    logger.info(f"Refreshing token for user {user_id}")
    new_access_token, new_refresh_token = refresh_access_token(refresh_token)
    if new_access_token:
        access_token = new_access_token
        refresh_token = new_refresh_token
        save_user_tokens(user_id, access_token, refresh_token)
        logger.info(f"Token refreshed for user {user_id}")
    else:
        logger.error(f"Failed to refresh token for user {user_id}")

    logger.info(f"Getting activities for user {user_id}")
    activities = get_athlete_activities(access_token)
    if activities:
        for activity in activities[:5]:  # Показываем только 5 последних активностей
            message = f"Тип: {activity['type']}\nДата: {activity['start_date_local']}\nНазвание: {activity['name']}\nРасстояние: {activity['distance'] / 1000:.2f} км\n"
            keyboard = [[InlineKeyboardButton("Нравится", callback_data=f"like_{activity['id']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Не удалось получить данные о ваших активностях.")
        logger.error(f"Failed to retrieve activities for user {user_id}")

def main() -> None:
    try:
        logger.info("Initializing bot")
        init_db()
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(auth_callback, pattern='^[0-9a-fA-F]{40}$'))
        application.add_handler(CommandHandler("activities", show_activities))

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

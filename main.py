import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from strava_auth import get_authorization_url, exchange_code_for_token, refresh_access_token
from strava_request import get_athlete_activities, get_activity_photos
import sqlite3

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, access_token TEXT, refresh_token TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS likes
                 (user_id INTEGER, activity_id TEXT, PRIMARY KEY (user_id, activity_id))''')
    conn.commit()
    conn.close()

# Сохранение токенов пользователя
def save_user_tokens(user_id, access_token, refresh_token):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, access_token, refresh_token) VALUES (?, ?, ?)",
              (user_id, access_token, refresh_token))
    conn.commit()
    conn.close()

# Получение токенов пользователя
def get_user_tokens(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT access_token, refresh_token FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None)

def start(update: Update, context: CallbackContext) -> None:
    auth_url = get_authorization_url()
    keyboard = [[InlineKeyboardButton("Авторизоваться в Strava", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Нажмите кнопку ниже, чтобы авторизоваться в Strava:', reply_markup=reply_markup)

def auth_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    code = query.data
    user_id = query.from_user.id

    access_token, refresh_token = exchange_code_for_token(code)
    save_user_tokens(user_id, access_token, refresh_token)

    query.answer()
    query.edit_message_text(text="Вы успешно авторизовались в Strava!")

def show_activities(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    access_token, refresh_token = get_user_tokens(user_id)

    if not access_token:
        update.message.reply_text("Пожалуйста, сначала авторизуйтесь в Strava.")
        return

    # Попробуем обновить токен перед использованием
    new_access_token, new_refresh_token = refresh_access_token(refresh_token)
    if new_access_token:
        access_token = new_access_token
        refresh_token = new_refresh_token
        save_user_tokens(user_id, access_token, refresh_token)

    activities = get_athlete_activities(access_token)
    if activities:
        for activity in activities[:5]:  # Показываем только 5 последних активностей
            message = f"Тип: {activity['type']}\n"
            message += f"Дата: {activity['start_date_local']}\n"
            message += f"Название: {activity['name']}\n"
            message += f"Расстояние: {activity['distance'] / 1000:.2f} км\n"
            
            keyboard = [[InlineKeyboardButton("Нравится", callback_data=f"like_{activity['id']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(message, reply_markup=reply_markup)
            
            photos = get_activity_photos(access_token, activity['id'])
            if photos:
                for photo in photos[:3]:  # Показываем до 3 фотографий
                    update.message.reply_photo(photo['urls']['600'])
    else:
        update.message.reply_text("Не удалось получить данные о ваших активностях.")

def like_activity(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    activity_id = query.data.split('_')[1]
    user_id = query.from_user.id

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO likes (user_id, activity_id) VALUES (?, ?)", (user_id, activity_id))
    conn.commit()
    conn.close()

    query.answer("Вам понравилась эта активность!")
    check_mutual_likes(update, context, user_id, activity_id)

def check_mutual_likes(update: Update, context: CallbackContext, user_id: int, activity_id: str) -> None:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM likes WHERE activity_id = ? AND user_id != ?", (activity_id, user_id))
    liked_users = c.fetchall()
    conn.close()

    for liked_user in liked_users:
        other_user_id = liked_user[0]
        if has_mutual_like(user_id, other_user_id):
            send_mutual_like_notification(update, context, user_id, other_user_id)

def has_mutual_like(user_id1: int, user_id2: int) -> bool:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM likes l1
        JOIN likes l2 ON l1.activity_id = l2.activity_id
        WHERE l1.user_id = ? AND l2.user_id = ?
    """, (user_id1, user_id2))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def send_mutual_like_notification(update: Update, context: CallbackContext, user_id1: int, user_id2: int) -> None:
    # Здесь нужно реализовать отправку уведомлений обоим пользователям
    # Это потребует дополнительной работы с API Telegram и Strava для получения профилей пользователей
    pass

def main() -> None:
    init_db()
    updater = Updater(os.environ.get("TELEGRAM_BOT_TOKEN"))

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(auth_callback, pattern='^[0-9a-fA-F]{40}$'))
    dp.add_handler(CommandHandler("activities", show_activities))
    dp.add_handler(CallbackQueryHandler(like_activity, pattern='^like_'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

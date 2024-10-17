from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# Токен телеграм бота
TELEGRAM_TOKEN = '7311543449:AAFY5nVhOwRJEbnJLHkTMskMFsGzXrKasXo'

# Strava данные
CLIENT_ID = '137731'  # Твой client_id от Strava
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'  # Твой client_secret от Strava

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я бот для взаимодействия со Strava.')

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Доступные команды:\n'
        '/start - Начать общение с ботом\n'
        '/help - Получить помощь\n'
        '/register - Регистрация через Strava\n'
        '/exchange_code <code> - Обмен кода на токен'
    )

# Команда /register (отправляет ссылку для авторизации в Strava)
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    auth_url = (
        'https://www.strava.com/oauth/authorize'
        '?client_id={client_id}&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=read,read_all,profile:read_all,activity:read_all'
    ).format(client_id=CLIENT_ID)
    await update.message.reply_text(f'Авторизуйся через Strava: {auth_url}')

# Команда /exchange_code (получает код и обменивает его на токен)
async def exchange_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:  # Проверка наличия аргументов
        code = context.args[0]  # Код, который вводит пользователь после авторизации
        url = 'https://www.strava.com/oauth/token'
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(url, data=payload)
        token_data = response.json()

        if 'access_token' in token_data:
            await update.message.reply_text(f"Твой токен: {token_data['access_token']}")
        else:
            await update.message.reply_text('Не удалось получить токен. Проверь правильность кода.')
    else:
        await update.message.reply_text('Пожалуйста, укажи код после команды.')

def main() -> None:
    # Создаём экземпляр Application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Добавляем команды
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('exchange_code', exchange_code))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

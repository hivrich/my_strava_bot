from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import os
import asyncio
import nest_asyncio

# Примените nest_asyncio, чтобы избежать ошибок
nest_asyncio.apply()

# Получаем токены из переменных окружения
TELEGRAM_TOKEN = '7311543449:AAFY5nVhOwRJEbnJLHkTMskMFsGzXrKasXo'
CLIENT_ID = '137731'
CLIENT_SECRET = '7257349b9930aec7f5c2ad6b105f6f24038e9712'

# URL для вебхука
WEBHOOK_URL = 'https://mystravabot-production.up.railway.app/webhook'

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

# Команда /register
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    auth_url = (
        'https://www.strava.com/oauth/authorize'
        '?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,read_all,profile:read_all,activity:read_all'
    ).format(client_id=CLIENT_ID, redirect_uri=WEBHOOK_URL)
    await update.message.reply_text(f'Авторизуйся через Strava: {auth_url}')

# Команда /exchange_code
async def exchange_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:  # Проверка наличия аргументов
        code = context.args[0]
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

async def main() -> None:
    # Создаём экземпляр Application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Добавляем команды
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('exchange_code', exchange_code))

    # Устанавливаем вебхук
    await application.bot.set_webhook(WEBHOOK_URL)

    # Запуск приложения в режиме вебхука
    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv('PORT', 8443)),
        url_path=TELEGRAM_TOKEN,
    )

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import nest_asyncio
import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

nest_asyncio.apply()

# Получаем токены из переменных окружения
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update, context):
    await update.message.reply_text('Привет! Я бот для взаимодействия со Strava.')

async def help_command(update, context):
    await update.message.reply_text('Команды: /start, /help, /activities')

async def activities(update, context):
    # Проверяем наличие access_token для Strava
    access_token = os.getenv('STRAVA_ACCESS_TOKEN')
    
    if not access_token:
        await update.message.reply_text('Ошибка: Необходим токен доступа Strava.')
        return

    # Получаем список активностей пользователя
    response = requests.get(
        f'https://www.strava.com/api/v3/athlete/activities',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if response.status_code == 200:
        activities = response.json()
        if activities:
            message = 'Ваши последние активности:\n'
            for activity in activities[:5]:  # показываем только последние 5 активностей
                message += f"{activity['name']} - {activity['distance']} м\n"
        else:
            message = 'У вас нет активностей.'
    else:
        message = 'Ошибка при получении активностей.'

    await update.message.reply_text(message)

async def main():
    if TELEGRAM_TOKEN is None:
        print("Ошибка: токен бота не установлен.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("activities", activities))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())

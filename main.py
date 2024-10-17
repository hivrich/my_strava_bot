import os
import asyncio
import nest_asyncio
import requests
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токены из переменных окружения
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update, context):
    logger.info("Bot started")
    await update.message.reply_text('Привет! Я бот для взаимодействия со Strava.')

async def help_command(update, context):
    await update.message.reply_text('Команды: /start, /help, /activities')

async def activities(update, context):
    access_token = os.getenv('STRAVA_ACCESS_TOKEN')
    
    if not access_token:
        await update.message.reply_text('Ошибка: Необходим токен доступа Strava.')
        return

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

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

async def main():
    if TELEGRAM_TOKEN is None:
        logger.error("Ошибка: токен бота не установлен.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("activities", activities))

    # Добавление обработчика ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())

# Получение списка активностей
def get_recent_activities_with_photos(access_token, limit=5):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(
        f"https://www.strava.com/api/v3/athlete/activities?per_page={limit}",
        headers=headers
    )
    if response.status_code == 200:
        activities = response.json()
        # Отбираем активности с фотографиями
        activities_with_photos = []
        for activity in activities:
            activity_id = activity.get("id")
            photos_response = requests.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}/photos",
                headers=headers
            )
            if photos_response.status_code == 200:
                photos = photos_response.json()
                if photos:  # Если есть фото, добавляем в результат
                    activity["photos"] = photos
                    activities_with_photos.append(activity)
        return activities_with_photos
    else:
        logger.error(f"Ошибка получения активностей: {response.text}")
        return None

# Обработка фотографий после авторизации
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]

        # Получаем данные пользователя
        athlete_data = get_strava_athlete_data(access_token)
        recent_activities = get_recent_activities_with_photos(access_token, limit=5)

        if athlete_data:
            athlete_name = f"{athlete_data['firstname']} {athlete_data['lastname']}"
            message = f"Вы успешно авторизовались в Strava! 🎉\nВаш профиль: {athlete_name}\n"
            
            if recent_activities:
                message += "Последние активности с фото:\n"
                for activity in recent_activities:
                    activity_name = activity["name"]
                    distance_km = activity["distance"] / 1000
                    photo_url = activity["photos"][0]["urls"]["600"]  # Берём фото первого размера 600
                    message += f"{activity_name} - {distance_km:.2f} км\nФото: {photo_url}\n\n"
            else:
                message += "У вас пока нет активностей с фото."

            await application.bot.send_message(
                chat_id=user_id,
                text=message,
            )
        else:
            await application.bot.send_message(
                chat_id=user_id,
                text="Ошибка получения данных пользователя Strava. Попробуйте позже.",
            )
        return "Авторизация прошла успешно. Вернитесь в Telegram!"
    else:
        return "Ошибка при авторизации в Strava.", 400

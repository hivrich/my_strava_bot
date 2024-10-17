import requests

# Ваш Access Token
access_token = 'fc86aea175c651a2856a46f300dafdaf361df44f'
# URL для запроса информации о пользователе
url = 'https://www.strava.com/api/v3/athlete'

# Заголовки запроса
headers = {
    'Authorization': f'Bearer {access_token}',
}

# Отправляем GET-запрос
response = requests.get(url, headers=headers)

# Проверяем, успешен ли запрос
if response.status_code == 200:
    # Если да, получаем данные о пользователе
    athlete_data = response.json()
    print(athlete_data)  # Печатаем информацию о пользователе
else:
    # Если возникла ошибка, печатаем код ошибки и сообщение
    print(f"Ошибка: {response.status_code}, {response.text}")

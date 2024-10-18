import requests
import os

def get_athlete_activities(access_token):
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
        return None

def get_activity_photos(access_token, activity_id):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/photos"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"size": "600"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
        return None

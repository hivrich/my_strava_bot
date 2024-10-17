import requests

CLIENT_ID = '137731'
CLIENT_SECRET = 'ВАШ_CLIENT_SECRET'  # Не забудь добавить свой Client Secret от Strava
REDIRECT_URI = 'http://localhost'

def exchange_code_for_token(code):
    url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(url, data=payload)
    return response.json()

if __name__ == '__main__':
    code = 'ВВЕДИ_КОД_ОТ_СТРАВЫ'
    token_data = exchange_code_for_token(code)
    print(token_data)

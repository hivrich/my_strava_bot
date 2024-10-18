import os
import requests

STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID', '137731')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET', '7257349b9930aec7f5c2ad6b105f6f24038e9712')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'https://mystravabot-production.up.railway.app/strava_callback')

def get_authorization_url():
    params = {
        'client_id': STRAVA_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'read,activity:read_all,profile:read_all'
    }
    return f"https://www.strava.com/oauth/authorize?{'&'.join(f'{k}={v}' for k, v in params.items())}"

def exchange_code_for_token(code):
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data['access_token'], data['refresh_token']
    else:
        return None, None

if __name__ == '__main__':
    print(get_authorization_url())

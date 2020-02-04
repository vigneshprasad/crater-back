import requests

from django.conf import settings

class InstagramService:

    def __init__(self, client_id, client_secret, redirect_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_url = redirect_url

    def get_short_access_token(self, code):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_url,
            'code': code
        }
        resp = requests.post('https://api.instagram.com/oauth/access_token/', data=data)
        if 'access_token' in resp.json():
            return resp.json()['access_token']
        else:
            return None

    def get_long_access_token(self, short_access_token):
        data = {
            'client_secret': self.client_secret,
            'grant_type': 'ig_exchange_token',
            'access_token': short_access_token
        }
        resp = requests.get('https://graph.instagram.com/access_token', paramsd=data)
        if 'access_token' in resp.json():
            return resp.json()['access_token']
        else:
            return None

    def convert_code_to_long_access_token(self, code):
        short_access_token = self.get_short_access_token(code=code)
        if not short_access_token:
            return None
        return self.get_long_access_token(short_access_token=short_access_token)

    @staticmethod
    def refresh_long_access_token(long_access_token):
        data = {
            'grant_type': 'ig_refresh_token',
            'access_token': long_access_token
        }
        resp = requests.get('https://graph.instagram.com/refresh_access_token', paramsd=data)
        if 'access_token' in resp.json():
            return resp.json()['access_token']
        else:
            return None

    @staticmethod
    def get_medias(long_access_token, limit=20):
        data = {
            'fields': 'id,media_url,thumbnail_url,media_type,caption,permalink,timestamp,username',
            'access_token': long_access_token,
            'limit': limit
        }
        resp = requests.get('https://graph.instagram.com/me/media', paramsd=data)
        return resp.json()['data']



instagram_service = InstagramService(
    client_id=settings.INSTAGRAM_API_CLIENT_ID,
    client_secret=settings.INSTAGRAM_API_CLIENT_SECRET,
    redirect_url=settings.INSTAGRAM_REDIRECT_URL
)

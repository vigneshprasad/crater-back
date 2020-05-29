import jwt
import requests
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .provider import AppleProvider


class AppleOAuth2Adapter(OAuth2Adapter):
    provider_id = AppleProvider.id
    access_token_url = 'https://appleid.apple.com/auth/token'

    def complete_login(self, request, app, token, **kwargs):
        data = self.apple_complete_login(request, app, token, **kwargs)
        return self.get_provider().sociallogin_from_response(request, data)

    def apple_complete_login(self, request, app, token, **kwargs):
        """
        Finish the auth process once the access_token was retrieved
        Get the email from ID token received from apple
        """
        is_web = kwargs.get('is_web', False)
        response_data = {}
        client_id, client_secret = self.get_key_and_secret(is_web=is_web)

        headers = {'content-type': "application/x-www-form-urlencoded"}
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': token.token,
            'grant_type': 'authorization_code'
        }

        res = requests.post(self.access_token_url, data=data, headers=headers)
        response_dict = res.json()
        id_token = response_dict.get('id_token', None)
        if id_token:
            decoded = jwt.decode(id_token, '', verify=False)
            response_data.update({'email': decoded['email']}) if 'email' in decoded else None
            response_data.update({'uid': decoded['sub']}) if 'sub' in decoded else None
        else:
            raise serializers.ValidationError(
                {
                    'access_token': _('Token is invalid')
                }
            )
        response_data.update({'access_token': response_dict['access_token']}) if 'access_token' not in response_dict else None
        return response_data

    @staticmethod
    def get_key_and_secret(is_web=False):
        apple_client_id = settings.SOCIAL_AUTH_WEB_APPLE_CLIENT_ID if is_web else settings.SOCIAL_AUTH_APPLE_CLIENT_ID
        headers = {
            'kid': settings.SOCIAL_AUTH_APPLE_KEY_ID
        }
        payload = {
            'iss': settings.SOCIAL_AUTH_APPLE_TEAM_ID,
            'iat': timezone.now(),
            'exp': timezone.now() + timezone.timedelta(days=180),
            'aud': 'https://appleid.apple.com',
            'sub': apple_client_id,
        }

        client_secret = jwt.encode(
            payload,
            settings.SOCIAL_AUTH_APPLE_PRIVATE_KEY,
            algorithm='ES256',
            headers=headers
        ).decode("utf-8")
        return apple_client_id, client_secret


oauth2_login = OAuth2LoginView.adapter_view(AppleOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(AppleOAuth2Adapter)

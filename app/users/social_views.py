from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_auth.registration.views import SocialLoginView, SocialConnectView

from .mixins import CheckDeviceMixin
from .serializers import SocialLoginSerializer


class GoogleLogin(SocialLoginView, CheckDeviceMixin):
    """
    https://accounts.google.com/o/oauth2/auth?&client_id=468382212295-5e5ti698mjf4oruhneavnob13r58b80e.apps.googleusercontent.com&redirect_uri=http://127.0.0.1:8001/oauth/complete/google-oauth2&response_type=token&scope=https://www.googleapis.com/auth/userinfo.email
    """
    adapter_class = GoogleOAuth2Adapter
    serializer_class = SocialLoginSerializer
    client_class = OAuth2Client
    callback_url = 'http://localhost:5000'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.check_device()
        return response


class FacebookLogin(SocialLoginView, CheckDeviceMixin):
    """
    https://www.facebook.com/v2.2/dialog/oauth?client_id=1866118480133387&redirect_uri=https://www.domain.com/login&display=popup&response_type=code%20token
    """
    adapter_class = FacebookOAuth2Adapter
    serializer_class = SocialLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.check_device()
        return response


class LinkedinLogin(SocialLoginView, CheckDeviceMixin):
    """
    https://www.facebook.com/v2.2/dialog/oauth?client_id=1866118480133387&redirect_uri=https://www.domain.com/login&display=popup&response_type=code%20token
    """
    # adapter_class = CustomFacebookOAuth2Adapter
    adapter_class = LinkedInOAuth2Adapter
    serializer_class = SocialLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        self.check_device()
        return response


class GoogleConnect(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter


class FacebookConnect(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter


class LinkedinConnect(SocialConnectView):
    adapter_class = LinkedInOAuth2Adapter


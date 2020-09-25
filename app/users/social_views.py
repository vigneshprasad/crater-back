from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client, OAuth2Error
from rest_auth.registration.views import SocialLoginView, SocialConnectView, \
    SocialAccountDisconnectView as DisconnectView, SocialAccountListView as AccountListView
from rest_framework import status
from rest_framework.response import Response

from users.appleid.views import AppleOAuth2Adapter
from .mixins import CheckDeviceMixin, CheckGroupMixin, CheckEmailMixin, SetIntentMixin, SetSourceMixin, \
    PhoneVerifiedMixin
from .serializers import SocialLoginSerializer, ConnectSerializer, AppleSocialLoginSerializer


class GoogleLogin(SocialLoginView, CheckDeviceMixin, CheckGroupMixin, CheckEmailMixin, SetIntentMixin, SetSourceMixin):
    """
    https://accounts.google.com/o/oauth2/auth?&client_id=468382212295-5e5ti698mjf4oruhneavnob13r58b80e.apps.googleusercontent.com&redirect_uri=http://127.0.0.1:8001/oauth/complete/google-oauth2&response_type=token&scope=https://www.googleapis.com/auth/userinfo.email
    """
    adapter_class = GoogleOAuth2Adapter
    serializer_class = SocialLoginSerializer
    client_class = OAuth2Client
    callback_url = 'http://localhost:5000'

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        self.check_device()
        self.check_group()
        self.check_email()
        self.set_intent()
        self.set_source()
        return self.get_response()


class FacebookLogin(SocialLoginView, CheckDeviceMixin, CheckGroupMixin, CheckEmailMixin, SetIntentMixin, SetSourceMixin):
    """
    https://www.facebook.com/v2.2/dialog/oauth?client_id=1866118480133387&redirect_uri=https://www.domain.com/login&display=popup&response_type=code%20token
    """
    adapter_class = FacebookOAuth2Adapter
    serializer_class = SocialLoginSerializer

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        self.check_device()
        self.check_group()
        self.check_email()
        self.set_intent()
        self.set_source()
        return self.get_response()


class LinkedinLogin(SocialLoginView, CheckDeviceMixin, CheckGroupMixin, CheckEmailMixin, SetIntentMixin, SetSourceMixin):
    """
    https://www.facebook.com/v2.2/dialog/oauth?client_id=1866118480133387&redirect_uri=https://www.domain.com/login&display=popup&response_type=code%20token
    """
    # adapter_class = CustomFacebookOAuth2Adapter
    adapter_class = LinkedInOAuth2Adapter
    serializer_class = SocialLoginSerializer
    callback_url = 'https://example.com/'
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        try:
            super().post(request, *args, **kwargs)
        except OAuth2Error:
            return Response({'code': 'Code is wrong or expired'}, status=status.HTTP_400_BAD_REQUEST)
        self.check_device()
        self.check_group()
        self.check_email()
        self.set_intent()
        self.set_source()
        return self.get_response()


class AppleLogin(SocialLoginView, CheckDeviceMixin, CheckGroupMixin, CheckEmailMixin, SetIntentMixin,
                 SetSourceMixin, PhoneVerifiedMixin):
    adapter_class = AppleOAuth2Adapter
    serializer_class = AppleSocialLoginSerializer

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        self.check_device()
        self.check_group()
        self.check_email()
        self.set_intent()
        self.set_source()
        self.set_phone_verified()
        self.set_fullname()
        return self.get_response()

    def set_fullname(self):
        first_name = self.serializer.validated_data.get('first_name', '')
        last_name = self.serializer.validated_data.get('last_name', '')
        name = self.serializer.validated_data.get('name', '')
        if first_name:
            self.user.first_name = first_name
        if last_name:
            self.user.last_name = last_name
        if first_name or last_name:
            self.user.name = f'{first_name} {last_name}'
            self.user.save()
        if name and not (first_name or last_name):
            self.user.name = name
            self.user.save()


class GoogleConnect(SocialConnectView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = ConnectSerializer


class FacebookConnect(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter
    serializer_class = ConnectSerializer


class LinkedinConnect(SocialConnectView):
    adapter_class = LinkedInOAuth2Adapter
    serializer_class = ConnectSerializer


class AppleConnect(SocialConnectView):
    adapter_class = AppleOAuth2Adapter
    serializer_class = ConnectSerializer


class SocialAccountDisconnectView(DisconnectView):

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return None
        return super().get_queryset()


class SocialAccountListView(AccountListView):

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return None
        return super().get_queryset()

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework_jwt import authentication


class JSONWebTokenAuthentication(authentication.JSONWebTokenAuthentication):

    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        User = get_user_model()

        try:
            user = User.objects.get(pk=payload['user_id'])
        except User.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user

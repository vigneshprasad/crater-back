import jwt

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_jwt.utils import jwt_decode_handler
from users.models import User


@database_sync_to_async
def get_user(token_key):
    if not token_key:
        return AnonymousUser()

    try:
        payload = jwt_decode_handler(token_key)
        user = User.objects.get(uuid=payload.get('user_id'))
        return user
    except (ValidationError, AuthenticationFailed, jwt.InvalidAlgorithmError, User.DoesNotExist):
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    Token authorization middleware using token query param
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope, *args, **kwargs):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        token_key = \
            (dict((x.split('=') for x in self.scope['query_string'].decode().split("&")))).get('token', None)

        self.scope['user'] = await get_user(token_key)
        inner = self.inner(self.scope)

        return await inner(receive, send)

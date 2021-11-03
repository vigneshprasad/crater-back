from urllib.parse import parse_qsl

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_jwt.utils import jwt_decode_handler
from users.models import User


@database_sync_to_async
def get_user(token_key):
    """Get user from token key.

    Args:
        token_key(JWT): JWT signature.

    """
    try:
        payload = jwt_decode_handler(token_key)
        user = User.objects.get(uuid=payload.get("user_id"))
    # TODO(Nishant): Replace this with concrete exceptions.
    except Exception:
        user = AnonymousUser()

    return user


class TokenAuthMiddleware:
    """Token authorization middleware using token query param."""

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope, *args, **kwargs):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    """Instance of Token auth middleware."""

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        token_key = dict(
            parse_qsl(
                self.scope["query_string"].decode()
            )
        ).get("token")

        # Set the user in the scope.
        self.scope["user"] = await get_user(token_key)
        inner = self.inner(self.scope)

        return await inner(receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))

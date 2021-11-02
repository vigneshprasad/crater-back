# mysite/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter

from consumers import routing
from consumers.middleware import TokenAuthMiddlewareStack

application = ProtocolTypeRouter({
    'websocket': TokenAuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})

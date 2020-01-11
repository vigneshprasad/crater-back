# chat/routing.py
from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:token>/', consumers.SupportConsumer),
    path('ws/chat/<str:user_id>/<str:token>/', consumers.ChatConsumer),
]

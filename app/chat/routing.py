from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/chat/user/<str:token>/', consumers.ChatConsumer),
    path('ws/chat/<str:token>/', consumers.ChatConsumer),
    path('ws/chat/<str:user_id>/<str:token>/', consumers.ChatConsumer),
]

from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/connector/<str:token>/', consumers.ChatConsumer),
    path('ws/connector/<str:receiver_id>/<str:token>/', consumers.ChatConsumer),
]

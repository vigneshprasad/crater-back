from django.urls import path

from conversations import consumers

websocket_urlpatterns = [
    path("ws/connector/group/<str:group_id>/", consumers.GroupChatConsumer),
]

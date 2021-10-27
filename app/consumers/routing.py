from django.urls import path

# from . import consumers
from conversations.consumers import GroupChatConsumer

websocket_urlpatterns = [
    path('ws/connector/group/<str:group_id>/', GroupChatConsumer),
]

# path('ws/connector/<str:token>/', consumers.ChatConsumer),
# path('ws/connector/<str:receiver_id>/<str:token>/', consumers.ChatConsumer),
# path('ws/connector/webinar/<str:group_id>/<str:token>/', consumers.LiveCountConsumer),

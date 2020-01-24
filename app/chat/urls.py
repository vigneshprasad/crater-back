from django.urls import path

from . import views
from .views import AdminChatFileView

urlpatterns = [
    path('', views.index, name='index'),
    # path('<str:user_id>/<str:token>/', views.chat, name='room'),
    path('support/<str:token>/', views.support, name='support'),
    path('users/<str:token>/', views.user_chat_page, name='users'),
    path('chat-file/', AdminChatFileView.as_view(), name='chat-file'),
]

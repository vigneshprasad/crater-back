from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('<str:user_id>/<str:token>/', views.chat, name='room'),
    path('support/<str:token>/', views.support, name='support'),
    path('users/<str:token>/', views.user_chat_page, name='users'),
    path('chat-file/', views.AdminChatFileView.as_view(), name='chat-file'),
]

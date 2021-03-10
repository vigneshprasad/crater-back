from django.urls import path, include
from rest_framework import routers

from integrations.agora import views

app_name = "agora"

router = routers.SimpleRouter()

router.register('', views.AgoraChannelAuthenticationViewSet, base_name="agora_rtc")

urlpatterns = [
    path('', include(router.urls))
]
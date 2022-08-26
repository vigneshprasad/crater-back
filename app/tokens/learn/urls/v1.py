from django.urls import path, include
from rest_framework import routers

from tokens.learn import views

app_name = "learn_tokens"

router = routers.SimpleRouter()

router.register("meta", views.UserLearnMetaViewSet, base_name="agora_rtc")

urlpatterns = [
    path("", include(router.urls))
]

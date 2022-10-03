from django.urls import path, include

from rest_framework import routers

from conversations.multistream import views

app_name = "multistream"

router = routers.SimpleRouter()

router.register("", views.MultiStreamViewSet, base_name="conversation_multistreams")

urlpatterns = [
    path("", include(router.urls)),
]
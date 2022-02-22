from django.urls import path, include
from rest_framework import routers

from integrations.firebase import views

app_name = "firebase"

router = routers.SimpleRouter()

router.register("", views.FirebaseViewSet, base_name="firebase")

urlpatterns = [
    path("", include(router.urls))
]

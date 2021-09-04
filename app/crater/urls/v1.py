from django.urls import path
from django.urls import include
from rest_framework.routers import DefaultRouter

from crater.auth import views as auth_views

app_name = "crater"

router = DefaultRouter()

# Auth endpoints for creator.
router.register("auth", auth_views.PhoneNumberRegisterView, base_name="crater-auth")

urlpatterns = [
    path("", include(router.urls))
]

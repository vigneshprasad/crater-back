from django.urls import path, include

from rest_framework import routers

from integrations.onesignal import views

app_name = "onesignal"

router = routers.SimpleRouter()

router.register("devices", views.OneSignalDeviceViewSet, basename="onesignal_device")

urlpatterns = [
    path("", include(router.urls))
]
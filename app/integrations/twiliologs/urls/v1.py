from django.urls import path, include
from rest_framework import routers

from integrations.twiliologs import views

app_name = "twilio"

router = routers.SimpleRouter()

router.register("", views.TwilioSMSViewSet, base_name="twilio-sms")

urlpatterns = [
    path("", include(router.urls))
]

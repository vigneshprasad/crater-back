from django.urls import path, include
from rest_framework import routers

from wn_analytics import views

app_name = "wn_analytics"

router = routers.SimpleRouter()

router.register("segment/", views.SegmentWebhookViewSet, base_name="segment_webhook")

urlpatterns = [
    path("", include(router.urls))
]

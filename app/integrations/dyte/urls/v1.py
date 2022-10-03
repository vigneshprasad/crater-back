from django.urls import path, include
from rest_framework import routers

from integrations.dyte import views


app_name = "dyte"

router = routers.SimpleRouter()

router.register("participant", views.DyteParticipantViewSet, base_name="dyte_participants")
router.register("meeting", views.DyteMeetingViewSet, base_name="dyte_meetings")
router.register("recording", views.DyteMeetingRecordingViewSet, base_name="dyte_recordings")
router.register("livestream", views.LiveStreamViewSet, base_name="dyte_live_stream")

urlpatterns = [
    path("", include(router.urls))
]

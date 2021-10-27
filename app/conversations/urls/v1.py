from django.urls import path, include
from rest_framework import routers

from conversations import views
from conversations import public_views

app_name = "group_meetings"

router = routers.SimpleRouter()

router.register("topic", views.TopicViewSet, base_name="group_meeting_categories")
router.register("groups", views.GroupsViewSet, base_name="group_meeting_groups")
router.register("optin", views.OptinViewSet, base_name="group_meeting_optin")
router.register("requests", views.RequestViewSet, base_name="group_meeting_requests")
router.register("recordings", views.GroupRecodingViewSet, base_name="group_recordings")
router.register("conversation/calendar", views.GroupCalendarViewSet, base_name="conversation_calendar")
router.register("conversations/webinars/all", views.AllGroupWebinarViewSet, base_name="conversation_webinars_all")
router.register("conversations/webinars", views.GroupWebinarViewSet, base_name="conversations_webinars")
router.register("conversations/categories", views.CategoryViewSet, base_name="conversations_categories")


# Public views for conversations.
public_router = routers.DefaultRouter()

public_router.register(
    "conversations/webinars",
    public_views.GroupWebinarPublicViewSet,
    base_name="conversations_webinars_public"
)

urlpatterns = [
    path("", include(router.urls)),
    path("public/", include(public_router.urls))
]

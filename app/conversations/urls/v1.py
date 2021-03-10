from django.urls import path, include
from rest_framework import routers

from conversations import views

app_name = 'group_meetings'

router = routers.SimpleRouter()

router.register("topic", views.TopicViewSet, base_name="group_meeting_categories")
router.register("groups", views.GroupsViewSet, base_name="group_meeting_groups")
router.register("optin", views.OptinViewSet, base_name="group_meeting_optin")

urlpatterns = [
    path('', include(router.urls))
]
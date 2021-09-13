from django.urls import path
from django.urls import include
from rest_framework.routers import DefaultRouter

from crater.auth import views as auth_views
from crater.creator import views as creator_views

app_name = "crater"

router = DefaultRouter()

# Auth endpoints for creator.
router.register("auth", auth_views.PhoneNumberRegisterView, base_name="crater-auth")


# Creator app endpoints.
router.register("creator", creator_views.CreatorViewSet, base_name="crater-creator")
router.register("community", creator_views.CommunityViewSet, base_name="crater-communities")
router.register("community/members", creator_views.CommunityMemberViewSet, base_name="crater-community-members")
router.register("followers", creator_views.FollowerViewSet, base_name="crater-followers")

urlpatterns = [
    path("", include(router.urls))
]

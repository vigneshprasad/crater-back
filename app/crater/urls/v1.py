from django.urls import path
from django.urls import include
from rest_framework.routers import DefaultRouter

from crater.auth import views as auth_views
from crater.creator import views as creator_views
from crater.rewards import views as reward_views

app_name = "crater"

router = DefaultRouter()

# Auth endpoints for creator.
router.register("auth", auth_views.PhoneNumberRegisterView, base_name="crater-auth")

# Creator app endpoints.
router.register("creator/s", creator_views.CreatorSlugViewSet, base_name="crater-creator-slug")
router.register("creator", creator_views.CreatorViewSet, base_name="crater-creator")
router.register("community/members", creator_views.CommunityMemberViewSet, base_name="crater-community-members")
router.register("community", creator_views.CommunityViewSet, base_name="crater-communities")
router.register("followers", creator_views.FollowerViewSet, base_name="crater-followers")
router.register("coins", creator_views.CoinsViewSet, base_name="creator-coins")

# Rewards/Redemption endpoints.
router.register("reward/type", reward_views.RewardTypeViewSet, base_name="reward-types")
router.register("reward", reward_views.RewardViewSet, base_name="rewards")
router.register("redemption", reward_views.RedemptionViewSet, base_name="redemptions")

urlpatterns = [
    path("", include(router.urls)),
]

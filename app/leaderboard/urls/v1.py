from django.urls import path, include
from rest_framework import routers

from leaderboard import views


app_name = "leaderboard"

router = routers.SimpleRouter()

router.register("challenges", views.ChallengeViewSet, base_name="crater_challenge")
router.register("leaderboards", views.LeaderboardViewSet, base_name="challenge_leaderboards")
router.register("user/leaderboards", views.UserLeaderboardViewSet, base_name="user_leaderboards")

urlpatterns = [
    path("", include(router.urls))
]

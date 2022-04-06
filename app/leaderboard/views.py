from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from leaderboard import models, serializers
from users import permissions


class ChallengeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Challenge.objects.filter(is_active=True)
    serializer_class = serializers.ChallengeSerializer


class LeaderboardViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Leaderboard.objects.filter(is_active=True)
    serializer_class = serializers.LeaderboardSerializer


class UserLeaderboardViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.UserLeaderboard.objects.filter(is_active=True)
    serializer_class = serializers.UserLeaderboardSerializer

    def retrieve(self, request, *args, **kwargs):
        leaderboard_id = kwargs.get("id")
        leaderboard = models.Leaderboard.objects.get(id=leaderboard_id)

        user_leaderboards = leaderboard.user_leaderboards.all().order_by("-minutes_spent")
        serializer = self.get_serializer(user_leaderboards, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

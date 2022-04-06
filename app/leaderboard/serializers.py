from rest_framework import serializers

from leaderboard import models


class LeaderboardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Leaderboard


class UserLeaderboardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserLeaderboard

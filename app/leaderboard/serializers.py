from rest_framework import serializers

from leaderboard import models


class ChallengeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Challenge
        fields = "__all__"


class LeaderboardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Leaderboard
        fields = "__all__"


class UserLeaderboardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserLeaderboard
        fields = "__all__"

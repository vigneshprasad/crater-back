from rest_framework import serializers
from django.contrib.auth import get_user_model

from leaderboard import models
from leaderboard import constants
from crater.creator import models as creator_models


class DurationTypeNameChoiceSerializer(serializers.ChoiceField):

    def to_representation(self, value):
        if not value:
            return None
        return self._choices[value]

class DurationTypeSerializer(serializers.ModelSerializer):
    name = DurationTypeNameChoiceSerializer(read_only=True, choices=constants.LEADERBOARD_DURATION_CHOICES)

    class Meta:
        model = models.DurationType
        fields = (
            "name",
            "id"
        )


class ChallengeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Challenge
        fields = "__all__"


class LeaderboardSerializer(serializers.ModelSerializer):
    duration_type_detail = DurationTypeSerializer(source="duration_type", read_only=True)

    class Meta:
        model = models.Leaderboard
        fields = (
            "id",
            "challenge",
            "start",
            "end",
            "duration_type",
            "participants",
            "is_active",
            "last_calculated_at",
            "duration_type_detail"
        )

class UserLeaderbaordUserSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(source="profile.photo", read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "name",
            "photo"
        )

class UserLeaderboardCreatorSerializdr(serializers.ModelSerializer):

    class Meta:
        model = creator_models.Creator
        fields = (
            "slug",
        )


class UserLeaderboardSerializer(serializers.ModelSerializer):
    user_detail = UserLeaderbaordUserSerializer(source="user", read_only=True)
    creator_detail = UserLeaderboardCreatorSerializdr(source="user.creator", read_only=True)

    class Meta:
        model = models.UserLeaderboard
        fields = (
            "id",
            "user",
            "leaderboard",
            "rank",
            "total_minutes",
            "is_active",
            "last_calculated_at",
            "user_detail",
            "creator_detail",
        )

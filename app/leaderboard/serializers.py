from django.contrib.auth import get_user_model
from rest_framework import serializers

from crater.creator import models as creator_models
from leaderboard import models, constants


class DurationTypeNameChoiceSerializer(serializers.ChoiceField):

    def to_representation(self, value):
        if not value:
            return None
        return self._choices[value]


class DurationTypeSerializer(serializers.ModelSerializer):

    name = DurationTypeNameChoiceSerializer(
        read_only=True,
        choices=constants.LEADERBOARD_DURATION_CHOICES
    )

    class Meta:
        model = models.DurationType
        fields = (
            "id",
            "name"
        )
        read_only_fields = fields


class ChallengeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Challenge
        fields = (
            "id",
            "name",
            "title",
            "description",
            "image",
            "start",
            "end",
            "rules",
            "is_active"
        )
        # Marking all the fields as readonly.
        read_only_fields = fields


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
        # Marking all the fields as readonly.
        read_only_fields = fields


class UserLeaderboardUserSerializer(serializers.ModelSerializer):

    photo = serializers.ImageField(source="profile.photo", read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "name",
            "photo"
        )
        # Marking all the fields as readonly.
        read_only_fields = fields


class UserLeaderboardCreatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = creator_models.Creator
        fields = ("slug", )
        read_only_fields = fields


class UserLeaderboardSerializer(serializers.ModelSerializer):

    user_detail = UserLeaderboardUserSerializer(source="user", read_only=True)
    creator_detail = UserLeaderboardCreatorSerializer(source="user.creator", read_only=True)

    class Meta:
        model = models.UserLeaderboard
        fields = (
            "id",
            "user",
            "leaderboard",
            "rank",
            "total_minutes",
            "is_active",
            "user_detail",
            "creator_detail",
        )
        read_only_fields = fields

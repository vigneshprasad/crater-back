import datetime

from rest_framework import serializers

from matching import models
from matching import public


class UserScoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserScore
        fields = (
            'user',
            'score'
        )


class UserToUserMatchScoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserToUserMatchScore
        fields = (
            'primary_user',
            'secondary_user',
            'score',
            'detailed_score'
        )

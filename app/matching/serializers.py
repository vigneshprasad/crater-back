from rest_framework import serializers

from matching import models


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
            'user',
            'matched_user',
            'score',
            'detailed_score'
        )

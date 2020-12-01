import datetime

from rest_framework import serializers

from matching import models


class MatchScoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MatchScore
        fields = (
            'user',
            'score'
        )


class PublicTopMatchesSerializer(serializers.Serializer):

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

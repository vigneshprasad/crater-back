import datetime

from rest_framework import serializers

from matching import models
from matching import public


class MatchScoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MatchScore
        fields = (
            'user',
            'score'
        )


class PublicTopMatchesSerializer(serializers.Serializer):

    all_score = serializers.SerializerMethodField()

    # final_score = serializers.SerializerMethodField()
    # interest_objective_to_tag_score = serializers.SerializerMethodField()
    # tag_to_tag_score = serializers.SerializerMethodField()
    # objective_to_objective_score = serializers.SerializerMethodField()
    # introduction_text_score = serializers.SerializerMethodField()

    @staticmethod
    def get_all_score(user):
        return public.get_top_matches_for_user(user)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

import nltk

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets

from users import permissions
from matching import constants
from matching import public
from matching import models
from matching import serializers

nltk.download('punkt')
nltk.download('wordnet')


class TopMatchesPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.UserToUserMatchScoreSerializer
    queryset = models.UserToUserMatchScore.objects.all()
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")
        try:
            user = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return Response(
                status=400,
                data={
                    "message": "Selected user is not valid."
                }
            )

        user_to_user_scores = models.UserToUserMatchScore.objects.filter(primary_user=user).order_by('score')
        final_response = []

        for user_to_user_score in user_to_user_scores:
            detailed_score = user_to_user_score.detailed_score or {}
            data = {
                'user_id': user_to_user_score.matched_user.pk,
                'email': user_to_user_score.matched_user.email,
                'match_score': user_to_user_score.score,
                constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE: detailed_score.get(constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE, 0),
                constants.TAG_TO_TAG_ENGINE: detailed_score.get(constants.TAG_TO_TAG_ENGINE, 0),
                constants.OBJECTIVE_TO_OBJECTIVE_ENGINE: detailed_score.get(constants.OBJECTIVE_TO_OBJECTIVE_ENGINE, 0),
                constants.INTRODUCTION_TEXT_ENGINE: detailed_score.get(constants.INTRODUCTION_TEXT_ENGINE, 0),
            }
            final_response.append(data)

        return Response(final_response)

    @action(
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        detail=False,
    )
    def user_info(self, request, *args, **kwargs):
        """Get user's info based on the algorithm."""
        user_id = request.query_params.get("user_id")
        try:
            user = get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return Response(
                status=400,
                data={
                    "message": "Selected user is not valid."
                }
            )
        user_info = public.get_user_info(user)

        return Response(user_info)


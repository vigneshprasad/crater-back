import nltk

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets

from users import permissions
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
    serializer_class = serializers.PublicTopMatchesSerializer
    queryset = models.MatchScore.objects.all()
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

        top_matches_data = public.get_top_matches_for_user(user)

        return Response(top_matches_data)

    @action(
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        detail=False,
    )
    def user_info(self, request, *args, **kwargs):
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

from users import permissions

from integrations.dyte import models as dyte_models
from conversations import models as conversation_models

from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import status
from rest_framework import mixins


class UserLearnMetaViewSet(
    mixins.ListModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = None

    def list(self, request, *args, **kwargs):
        user = request.user
        participants = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group__host__creator__tokens_enabled=True,
            participant=user
        )

        total_time_spent = 0

        for participant in participants:
            total_time_spent += participant.total_minutes_watched

        interactions = conversation_models.GroupMessage.objects.filter(
            group__host__creator__tokens_enabled=True,
            sender=user,
        ).count()

        learn_earned = total_time_spent + (2 * interactions)

        result = {
            "total_time_spent": total_time_spent,
            "interactions": interactions,
            "learn_earned": learn_earned,
        }

        return Response(result, status=status.HTTP_200_OK)

import datetime

from users import permissions
from django.db.models import Sum

from integrations.dyte import models as dyte_models
from conversations import models as conversation_models

from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import status
from rest_framework import mixins

from tokens.learn import constants
from tokens import models as token_models
from tokens import constants as token_constants


class UserLearnMetaViewSet(
    mixins.ListModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = None

    def list(self, request, *args, **kwargs):

        user = request.user
        now = datetime.datetime.now()
        token_start_date = constants.LEARN_TOKEN_START_DATE

        if user.is_creator:
            return Response(
                {
                    "total_time_spent": 0,
                    "interactions": 0,
                    "learn_earned": 0,
                    "daily_learn_earned": 0,
                    "learn_burned": 0
                },
                status=status.HTTP_200_OK
            )

        participants = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group__host__creator__tokens_enabled=True,
            participant=user,
            dyte_meeting__group__start__gte=token_start_date
        )

        daily_participants = participants.filter(
            dyte_meeting__group__start__date=now.date()
        )

        total_time_spent = 0
        daily_total_time_spent = 0

        for participant in participants:
            total_time_spent += participant.total_minutes_watched

        for participant in daily_participants:
            daily_total_time_spent += participant.total_minutes_watched

        learn_burned = token_models.UserTokenLog.objects.filter(
            user=user,
            type=token_constants.TRANSACTION_TYPE_REDEEMED_ENUM
        ).aggregate(
            total_amount=Sum("amount")
        )["total_amount"] or 0

        interactions = conversation_models.GroupMessage.objects.filter(
            group__host__creator__tokens_enabled=True,
            sender=user,
            group__start__gte=token_start_date
        ).count()

        daily_interactions = conversation_models.GroupMessage.objects.filter(
            group__host__creator__tokens_enabled=True,
            sender=user,
            created_at__date=now.date(),
            group__start__gte=token_start_date
        ).count()

        learn_earned = total_time_spent + (2 * interactions)
        daily_learn_earned = daily_total_time_spent + (2 * daily_interactions)

        result = {
            "total_time_spent": total_time_spent,
            "interactions": interactions,
            "learn_earned": learn_earned,
            "daily_learn_earned": daily_learn_earned,
            "learn_burned": learn_burned
        }

        return Response(result, status=status.HTTP_200_OK)

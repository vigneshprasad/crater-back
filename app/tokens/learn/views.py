from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from conversations import models as conversation_models
from integrations.dyte import models as dyte_models
from tokens import constants as token_constants, models as token_models, public as tokens_public
from users import permissions as user_permissions


class UserLearnMetaViewSet(
    mixins.ListModelMixin,
    GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    queryset = None

    def list(self, request, *args, **kwargs):
        """Returns tokens earned, burned, total minutes spent and
            total engagement on the platform for a user.

        Note:
            This API is updated every 5 minutes instead of real time.

        """
        user = request.user
        now = timezone.now()
        today = now.date()
        yesterday = today - timezone.timedelta(days=1)

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

        total_tokens = tokens_public.get_tokens_for_user(user, yesterday)
        total_time_spent = 0
        total_engagement = 0

        user_token_logs = token_models.UserTokenLog.objects.filter(
            user=user,
            transaction__isnull=False,
            type=token_constants.TRANSACTION_TYPE_ACQUIRED_ENUM
        )
        for token_log in user_token_logs:
            total_time_spent += token_log.transaction.time_spent
            total_engagement += token_log.transaction.engagement

        # Calculate for today.
        today_learn_groups = conversation_models.Group.objects.filter(
            start__date=today,
            host__creator__tokens_enabled=True
        )
        user_dyte_participants_for_today = dyte_models.DyteMeetingParticipant.objects.filter(
            participant=user,
            dyte_meeting__group__in=today_learn_groups
        )
        minutes_spent_for_today = 0
        for user_dyte_participant_for_today in user_dyte_participants_for_today:
            minutes_spent_for_today += float(user_dyte_participant_for_today.minutes_spent)

        engagement_for_today = conversation_models.GroupMessage.objects.filter(
            group__in=today_learn_groups,
            sender=user
        ).count()

        today_learn_earned = (minutes_spent_for_today + (2 * engagement_for_today))
        total_learn_earned = total_tokens + today_learn_earned

        result = {
            "total_time_spent": total_time_spent + minutes_spent_for_today,
            "interactions": total_engagement + engagement_for_today,
            "learn_earned": total_learn_earned,
            "daily_learn_earned": today_learn_earned,
            "learn_burned": tokens_public.get_tokens_redeemed_by_user(user)
        }

        return Response(result, status=status.HTTP_200_OK)

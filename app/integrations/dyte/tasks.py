import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

from conversations import models as conversations_models
from integrations.dyte import models, service

dyte_service = service.dyte_service


@periodic_task(run_every=crontab("*/5"))
def get_minutes_for_live_streams():
    """Get minutes of live streams from Dyte's end and update on
        our models.

    Note:
        Updates the DyteMeetingParticipant and stream.total_minutes
            from Dyte's end.

    """
    now = timezone.now()
    live_groups = conversations_models.Group.objects.filter(
        is_live=True,
        is_published=True,
        closed=False,
        start__lte=now
    )

    for group in live_groups:
        stats = dyte_service.get_stats_for_meeting(group)
        for stat in stats:
            user_pk = stat["clientSpecificId"]
            total_minutes = stat["totalMinutes"]

            try:
                dyte_participant = models.DyteMeetingParticipant.objects.get(
                    dyte_meeting__group=group,
                    participant_id=user_pk
                )
            except models.DyteMeetingParticipant.DoesNotExist:
                continue

            dyte_participant.minutes_spent = total_minutes
            dyte_participant.save()


@periodic_task(run_every=crontab(hour="5", minute="30"))
def get_minutes_for_all_streams_for_the_day():
    """Get minutes of yesterday's streams from Dyte's end and update on
        our models.

    Note:
        Updates the DyteMeetingParticipant and stream.total_minutes
            from Dyte's end.

    """
    today = timezone.now()
    yesterday = today - datetime.timedelta(days=1)
    groups_in_the_last_day = conversations_models.Group.objects.filter(
        is_published=True,
        closed=True,
        start__lte=today,
        start__gte=yesterday
    )

    for group in groups_in_the_last_day:

        stats = dyte_service.get_stats_for_meeting(group)
        total_minutes_spent = 0
        for stat in stats:
            user_pk = stat["clientSpecificId"]
            total_minutes = stat["totalMinutes"]

            try:
                dyte_participant = models.DyteMeetingParticipant.objects.get(
                    dyte_meeting__group=group,
                    participant_id=user_pk
                )
            except models.DyteMeetingParticipant.DoesNotExist:
                continue

            dyte_participant.minutes_spent = total_minutes
            dyte_participant.save()
            total_minutes_spent += total_minutes

        group.total_minutes_spent = total_minutes_spent
        group.save()

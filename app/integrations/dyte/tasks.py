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
        total_minutes_spent_by_attendees = 0
        total_minutes_spent_by_host = 0

        if not stats:
            continue

        host_total_minutes = 0
        for stat in stats:
            if stat["clientSpecificId"] != str(group.host_id):
                continue
            host_total_minutes = stat["totalMinutes"]

        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

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

            total_minutes = min(total_minutes, host_total_minutes)
            # Add dyte minutes to the dyte participant object.
            dyte_participant.minutes_spent = total_minutes
            dyte_participant.save()

            # Add host and attendee minutes separately.
            if dyte_participant.participant == group.host:
                total_minutes_spent_by_host += total_minutes
            else:
                total_minutes_spent_by_attendees += total_minutes

        # Add these minutes to the group object.
        group.total_minutes_spent_by_attendees = total_minutes_spent_by_attendees
        group.total_minutes_spent_by_host = total_minutes_spent_by_host
        group.save()


@periodic_task(run_every=crontab(hour="00", minute="00"))
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
        total_minutes_spent_by_attendees = 0
        total_minutes_spent_by_host = 0

        if not stats:
            continue

        host_total_minutes = 0
        for stat in stats:
            if stat["clientSpecificId"] != str(group.host_id):
                continue
            host_total_minutes = stat["totalMinutes"]

        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

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

            total_minutes = min(total_minutes, host_total_minutes)
            # Add dyte minutes to the dyte participant object.
            dyte_participant.minutes_spent = total_minutes
            dyte_participant.save()

            # Add host and attendee minutes separately.
            if dyte_participant.participant == group.host:
                total_minutes_spent_by_host += total_minutes
            else:
                total_minutes_spent_by_attendees += total_minutes

        # Add these minutes to the group object.
        group.total_minutes_spent_by_attendees = total_minutes_spent_by_attendees
        group.total_minutes_spent_by_host = total_minutes_spent_by_host
        group.save()

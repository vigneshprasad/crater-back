import datetime

from celery.schedules import crontab
from celery.task import periodic_task, task
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
        dyte_participant_for_host = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not dyte_participant_for_host:
            continue

        dyte_participants_for_attendees = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            last_online_at__isnull=False
        ).exclude(id=dyte_participant_for_host.id)

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        minutes_spent_by_attendees = 0

        for dyte_participant in dyte_participants_for_attendees:
            minutes_spent = min(dyte_participant.total_minutes_watched, host_total_minutes)
            minutes_spent_by_attendees += minutes_spent
            # Update the minutes on Dyte participant.
            dyte_participant.minutes_spent = minutes_spent
            dyte_participant.save()

        # Add attendees and host minutes to the group.
        group.total_minutes_spent_by_attendees = minutes_spent_by_attendees
        group.total_minutes_spent_by_host = host_total_minutes
        group.save()


@periodic_task(run_every=crontab(hour="0", minute="0"))
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
        dyte_participant_for_host = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not dyte_participant_for_host:
            continue

        dyte_participants_for_attendees = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            last_online_at__isnull=False
        ).exclude(id=dyte_participant_for_host.id)

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        minutes_spent_by_attendees = 0

        for dyte_participant in dyte_participants_for_attendees:
            minutes_spent = min(dyte_participant.total_minutes_watched, host_total_minutes)
            minutes_spent_by_attendees += minutes_spent
            # Update the minutes on Dyte participant.
            dyte_participant.minutes_spent = minutes_spent
            dyte_participant.save()

        # Add attendees and host minutes to the group.
        group.total_minutes_spent_by_attendees = minutes_spent_by_attendees
        group.total_minutes_spent_by_host = host_total_minutes
        group.save()


@task()
def recalculate_minutes_for_groups(group_ids):
    """Get minutes of live streams from Dyte's end and update on
        our models.

    Args:
        group_ids(list/queryset): Group ids we want to recalculate
            minutes for.

    Note:
        Updates the DyteMeetingParticipant and stream.total_minutes
            from Dyte's end.

    """
    groups = conversations_models.Group.objects.filter(
        id__in=group_ids
    )

    for group in groups:
        dyte_participant_for_host = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            participant_id=group.host_id
        ).first()

        if not dyte_participant_for_host:
            continue

        dyte_participants_for_attendees = models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=group,
            last_online_at__isnull=False
        ).exclude(id=dyte_participant_for_host.id)

        host_total_minutes = dyte_participant_for_host.total_minutes_watched
        # If there are no host minutes, don't calculate minutes for
        # stream.
        if not host_total_minutes:
            continue

        minutes_spent_by_attendees = 0

        for dyte_participant in dyte_participants_for_attendees:
            minutes_spent = min(dyte_participant.total_minutes_watched, host_total_minutes)
            minutes_spent_by_attendees += minutes_spent
            # Update the minutes on Dyte participant.
            dyte_participant.minutes_spent = minutes_spent
            dyte_participant.save()

        # Add attendees and host minutes to the group.
        group.total_minutes_spent_by_attendees = minutes_spent_by_attendees
        group.total_minutes_spent_by_host = host_total_minutes
        group.save()

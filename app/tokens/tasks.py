import datetime

import pytz
from celery.task import task
from django.conf import settings

from conversations import models as conversations_models
from integrations.dyte import models as dyte_models
from tokens import constants, models


# @periodic_task(run_every=crontab(hour=18, minute=15))
def calculate_tokens_earned(date=None):
    """Calculates tokens earned for streams per day.

    Args:
        date(str): Date string we want to calculate tokens
            data for.
    Returns:
        total_time_spent(float/int): Total time spent across the date
        total_engagement(float/int): Total engagement across the date

    """

    if not date:
        today = datetime.date.today()
        today_start = datetime.datetime.combine(today, datetime.time())
        today_end = datetime.datetime.combine(today, datetime.time(23, 59))
        # Make datetime timezone aware.
        timezone = pytz.timezone(settings.TIME_ZONE)
        today_start = timezone.localize(today_start)
        today_end = timezone.localize(today_end)
    else:
        today = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        today_start = datetime.datetime.combine(today, datetime.time())
        today_end = datetime.datetime.combine(today, datetime.time(23, 59))
        # Make datetime timezone aware.
        timezone = pytz.timezone(settings.TIME_ZONE)
        today_start = timezone.localize(today_start)
        today_end = timezone.localize(today_end)

    # Only get streams whose hosts are eligible for learn tokens.
    streams_for_today = conversations_models.Group.objects.filter(
        start__gte=today_start,
        end__lte=today_end,
        host__creator__tokens_enabled=True,
    )

    return calculate_tokens_for_groups(
        list(streams_for_today.values_list("id", flat=True))
    )


@task()
def calculate_tokens_for_groups(group_ids):
    """Calculates tokens earned for streams per day.

    Args:
        group_ids(list/queryset): List of ids of the groups we
            are calculating the tokens for.

    Returns:
        total_time_spent(float/int): Total time spent across the groups
        total_engagement(float/int): Total engagement across the groups

    """

    total_time_spent, total_engagement = 0, 0
    for group_id in group_ids:
        time_spent, engagement = calculate_tokens_for_group(group_id)
        total_time_spent += time_spent
        total_engagement += engagement

    return total_time_spent, total_engagement


@task()
def calculate_tokens_for_group(group_id):
    """Calculates tokens earned for streams per day.

    Args:
        group_id(int): ID of the group we are calculating the
            tokens for.

    Returns:
        total_time_spent(float/int): Total time spent across the group
        total_engagement(float/int): Total engagement across the group.

    """
    total_engagement = 0
    total_watch_time = 0

    stream = conversations_models.Group.objects.get(id=group_id)
    host = stream.host
    if not host:
        return total_watch_time, total_engagement

    creator = host.creator if hasattr(host, "creator") else None
    if not creator:
        return total_watch_time, total_engagement

    if not creator.tokens_enabled:
        return total_watch_time, total_engagement

    print("Calculating data for stream: {}".format(stream))
    date = stream.start.date()
    dyte_participants_for_group = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group=stream,
        last_online_at__isnull=False
    )
    total_chat_for_stream = conversations_models.GroupMessage.objects.filter(group=stream)

    # Calculate tokens for host.
    host_dyte_participant = dyte_participants_for_group.filter(participant=host).last()
    if not host_dyte_participant:
        return total_watch_time, total_engagement

    streamer_time_spent = host_dyte_participant.minutes_spent
    if not streamer_time_spent:
        return total_watch_time, total_engagement

    streamer_engagement = total_chat_for_stream.filter(sender=host).count()
    # Add extra watch time to creator.
    streamer_time_spent += constants.EXTRA_WATCH_TIME_FOR_CREATOR_PER_STREAM
    # Add it to total for the day.
    total_engagement += streamer_engagement
    total_watch_time += streamer_time_spent

    # Create token transaction for host and stream.
    models.TokenTransaction.objects.update_or_create(
        user=host,
        stream=stream,
        type=constants.USER_TYPE_STREAMER_ENUM,
        defaults={
            "time_spent": streamer_time_spent,
            "engagement": streamer_engagement,
            "amount": streamer_time_spent + (streamer_engagement * 2),
            "date": date
        },
    )

    # Get all participants that attended the meeting, except for host.
    dyte_participants = dyte_participants_for_group.exclude(participant=stream.host)

    for dyte_participant in dyte_participants:
        attendee = dyte_participant.participant
        attendee_time_spent = dyte_participant.minutes_spent
        attendee_engagement = total_chat_for_stream.filter(sender=attendee).count()

        # If engagement and time spent are not there (zero), don't create
        # transactions.
        if not (attendee_engagement and attendee_time_spent):
            continue

        # Create a token transaction for each user and stream.
        models.TokenTransaction.objects.update_or_create(
            user=attendee,
            stream=stream,
            type=constants.USER_TYPE_ATTENDEE_ENUM,
            defaults={
                "time_spent": attendee_time_spent,
                "engagement": attendee_engagement,
                "amount": attendee_time_spent + (attendee_engagement * 2),
                "date": date
            }
        )

        # Update the total watch time with attendee watch time.
        total_watch_time += attendee_time_spent
        total_engagement += attendee_engagement

    return total_watch_time, total_engagement

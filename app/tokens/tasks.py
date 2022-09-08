import datetime

import pytz
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings

from conversations import models as conversations_models
from integrations.dyte import models as dyte_models
from tokens import constants, models


@periodic_task(run_every=crontab(hour=18, minute=15))
def calculate_tokens_earned(date=None):
    """Calculates tokens earned for streams per day.

    Args:
        date(str): Date string we want to calculate tokens
            data for.

    """

    if not date:
        today = datetime.date.today()
        today_start = datetime.datetime.combine(datetime.date.today(), datetime.time())
        today_end = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 59))
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

    participants_went_online_across_streams = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__groups=streams_for_today,
        last_online_at__isnull=False
    )
    total_chat_across_streams = conversations_models.GroupMessage.objects.filter(
        group__in=streams_for_today,
        created_at__gte=today_start,
        created_at__lte=today_end
    )

    total_engagement = total_chat_across_streams.count()
    total_watch_time = 0

    for stream in streams_for_today:
        # All dyte participants for a stream.
        participants_went_online_for_stream = participants_went_online_across_streams.filter(dyte_meeting__group=stream)
        # TODO(Nishant): Should we exclude creator messages from this.
        chat_for_stream = total_chat_across_streams.filter(group=stream).count()

        # Calculate tokens for host.
        host = stream.host
        host_dyte_participant = participants_went_online_for_stream.filter(participant=host).last()
        if not host_dyte_participant:
            continue

        streamer_time_spent = host_dyte_participant.total_minutes_watched
        if not streamer_time_spent:
            continue

        # Create token transaction for host and stream.
        models.TokenTransaction.objects.update_or_create(
            user=host,
            stream=stream,
            type=constants.USER_TYPE_STREAMER_ENUM,
            defaults={
                "time_spent": streamer_time_spent,
                "engagement": chat_for_stream,
                "amount": streamer_time_spent + (chat_for_stream * 2),
                "date": today
            },
        )

        # Get all participants that attended the meeting, except for host.
        dyte_participants = participants_went_online_for_stream.exclude(participant=stream.host)

        for dyte_participant in dyte_participants:
            attendee = dyte_participant.participant
            attendee_time_spent = dyte_participant.total_minutes_watched
            attendee_engagement = chat_for_stream.filer(sender=attendee).count()

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
                    "date": today
                }
            )

            total_watch_time += attendee_time_spent

    # Calculate token data per day for all attendees.
    models.TokenDataPerDay.objects.update_or_create(
        date=today,
        defaults={
            "time_spent": total_watch_time,
            "engagement": total_engagement,
            "amount": total_watch_time + (total_engagement * 2)
        }
    )

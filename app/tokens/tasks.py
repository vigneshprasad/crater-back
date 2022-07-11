import datetime
import logging

import boto3
from celery.schedules import crontab
from celery.task import periodic_task
from celery.task import task
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from conversations import models as conversations_models
from tokens import models
from integrations.dyte import models as dyte_models


@periodic_task(run_every=crontab(hour=18, minute=15))
def calculate_tokens_earned(streams=None):
    """Calculates tokens earned for streams per day.

    Args:
        streams(queryset/list): Streams we want to calculate tokens for.

    """
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time())
    today_end = datetime.datetime.combine(datetime.date.today(), datetime.time(11, 59))

    # Only get streams whose hosts are eligible for learn tokens.
    streams_for_today = conversations_models.Group.objects.filter(
        start__gte=today_start,
        end__lte=today_end,
        host__creator__isnull=False,
        host__creator__learn_tokens_enabled=True,
    ) if not streams else streams

    total_watch_time = streams_for_today.aggregate(total_minutes=Sum("total_minutes_spent_by_attendees"))["total_minutes"]

    total_engagement = conversations_models.GroupMessage.objects.filter(
        group__in=streams_for_today,
        created_at__gte=today_start,
        created_at__lte=today_end,
    ).count()

    # Calculate token data per day for all attendees.
    models.TokenDataPerDay.objects.create(
        date=datetime.date.today(),
        time_spent=total_watch_time,
        engagement=total_engagement,
        amount=total_watch_time + (total_engagement * 2)
    )

    for stream in streams_for_today:
        # Calculate tokens distributed for the streamer first.
        host = stream.host
        creator = None
        if host.is_creator:
            creator = host.creator

        streamer_time_spent = stream.total_minutes_spent_by_attendees
        if not streamer_time_spent:
            continue
        streamer_engagement = conversations_models.GroupMessage.objects.filter(
            group=stream
        ).count()

        # Create token transaction for host and stream.
        models.TokenTransaction.objects.get_or_create(
            user=host,
            creator=creator,
            stream=stream,
            time_spent=streamer_time_spent,
            engagement=streamer_engagement,
            amount=streamer_time_spent + (streamer_engagement * 2),
            type=models.TokenTransaction.USER_TYPE[1][0],
            date=datetime.date.today()
        )

        # Calculate tokens for all attendees.
        attendees = stream.attendees.all()
        # Get all participants that attended the meeting.
        dyte_participants = dyte_models.DyteMeetingParticipant.objects.filter(
            dyte_meeting__group=stream,
            participant__in=attendees,
            last_online_at__isnull=False
        )

        for dyte_participant in dyte_participants:
            attendee = dyte_participant.participant
            attendee_time_spent = dyte_participant.total_minutes_watched()
            attendee_engagement = conversations_models.GroupMessage.objects.filter(
                sender=attendee,
                group=stream
            ).count()

            # Create a token transaction for each user and stream.
            models.TokenTransaction.objects.get_or_create(
                user=attendee,
                stream=stream,
                creator=creator,
                time_spent=attendee_time_spent,
                engagement=attendee_engagement,
                amount=attendee_time_spent + (attendee_engagement * 2),
                type=models.TokenTransaction.USER_TYPE[0][0],
                date=datetime.date.today()
            )

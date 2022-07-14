import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.db.models import Sum

from conversations import models as conversations_models
from integrations.dyte import models as dyte_models
from tokens import models, constants


def calculate_tokens_earned_for_date(date):
    """Calculates tokens earned for streams for the
        given date.

    Args:
        date(str): Date string we want to calculate tokens
            data for.

    """
    date = datetime.datetime.strptime(date, "%d/%m/%y").date()
    date_start = datetime.datetime.combine(date, datetime.time())
    date_end = datetime.datetime.combine(date, datetime.time(11, 59))

    # Only get streams whose hosts are eligible for learn tokens.
    streams_for_today = conversations_models.Group.objects.filter(
        start__gte=date_start,
        end__lte=date_end,
        host__creator__isnull=False,
        host__creator__tokens_enabled=True,
    )

    total_watch_time = streams_for_today.aggregate(
        total_minutes=Sum("total_minutes_spent_by_attendees")
    )["total_minutes"]

    total_engagement = conversations_models.GroupMessage.objects.filter(
        group__in=streams_for_today,
        created_at__gte=date_start,
        created_at__lte=date_end,
    ).count()

    # Calculate token data per day for all attendees.
    models.TokenDataPerDay.objects.update_or_create(
        date=date,
        defaults={
            "time_spent": total_watch_time,
            "engagement": total_engagement,
            "amount": total_watch_time + (total_engagement * 2)
        }
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


@periodic_task(run_every=crontab(hour=18, minute=15))
def calculate_tokens_earned():
    """Calculates tokens earned for streams per day."""
    today = datetime.date.today()
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time())
    today_end = datetime.datetime.combine(datetime.date.today(), datetime.time(11, 59))

    # Only get streams whose hosts are eligible for learn tokens.
    streams_for_today = conversations_models.Group.objects.filter(
        start__gte=today_start,
        end__lte=today_end,
        host__creator__isnull=False,
        host__creator__tokens_enabled=True,
    )

    total_watch_time = streams_for_today.aggregate(
        total_minutes=Sum("total_minutes_spent_by_attendees")
    )["total_minutes"]

    total_engagement = conversations_models.GroupMessage.objects.filter(
        group__in=streams_for_today,
        created_at__gte=today_start,
        created_at__lte=today_end,
    ).count()

    # Calculate token data per day for all attendees.
    models.TokenDataPerDay.objects.update_or_create(
        date=today,
        defaults={
            "time_spent": total_watch_time,
            "engagement": total_engagement,
            "amount": total_watch_time + (total_engagement * 2)
        }
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
        models.TokenTransaction.objects.update_or_create(
            user=host,
            stream=stream,
            type=constants.USER_TYPE_STREAMER_ENUM,
            defaults={
                "time_spent": streamer_time_spent,
                "engagement": streamer_engagement,
                "amount": streamer_time_spent + (streamer_engagement * 2),
                "date": today
            },
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

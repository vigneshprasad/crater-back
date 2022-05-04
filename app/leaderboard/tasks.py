import datetime

from celery.schedules import crontab
from celery.task import periodic_task, task
from django.db.models import Sum
from django.utils import timezone

from conversations import models as conversations_models
from leaderboard import constants, private, models


@periodic_task(run_every=crontab("*/15"))
def update_user_leaderboards():
    """Update user leaderboards total minutes every
        15 minutes.

    """
    # Get all active leaderboards.
    leaderboards = private.get_active_leaderboards()
    # Get leaderboard that ended yesterday and update the final results.
    leaderboards_ended_yesterday = private.get_recently_ended_leaderboards()

    all_leaderboards_to_be_updated = leaderboards | leaderboards_ended_yesterday

    for leaderboard in all_leaderboards_to_be_updated:
        user_leaderboards = leaderboard.user_leaderboards.filter(is_active=True)

        for user_leaderboard in user_leaderboards:
            host = user_leaderboard.user
            groups_minute_aggregate = conversations_models.Group.objects.filter(
                host=host,
                start__gte=leaderboard.start,
                end__lte=leaderboard.end
            ).aggregate(minutes=Sum("total_minutes_spent_by_attendees"))
            minutes = groups_minute_aggregate["minutes"] or 0

            user_leaderboard.total_minutes = round(minutes, 2)
            user_leaderboard.last_calculated_at = timezone.now()
            user_leaderboard.save()

        leaderboard.last_calculated_at = timezone.now()


@task
def create_leaderboards_for_challenge(challenge_id):
    """Creates leaderboard on a Challenge creation for the provided durations.

    Args:
        challenge_id(int): ID of challenge object that was created.

    """
    challenge = models.Challenge.objects.get(id=challenge_id)
    duration_types = challenge.duration_types.all()

    for duration_type in duration_types:

        duration = constants.DURATION_TYPE_TO_DAYS_MAP[duration_type.name]
        start = challenge.start
        end = start + datetime.timedelta(days=duration)

        models.Leaderboard.objects.get_or_create(
            challenge=challenge,
            duration_type=duration_type,
            start=start,
            end=end
        )


@task
def create_user_leaderboards_for_leaderboard(leaderboard_id):
    """Creates leaderboard on a Challenge creation for the provided durations.

    Args:
        leaderboard_id(int): ID of challenge object that was created.

    """
    leaderboard = models.Leaderboard.objects.get(id=leaderboard_id)
    participants = leaderboard.challenge.participants.all()
    # Add challenge participants to the leaderboard.
    leaderboard.participants.add(*participants)

    for participant in participants:
        models.UserLeaderboard.objects.get_or_create(
            user=participant,
            leaderboard=leaderboard
        )


@task
def add_challenge_participants(leaderboard_ids):
    """Add challenge participants to leaderboard from challenge.

    Args:
        leaderboard_ids(list): List of leaderboard ids for which
            we have to add participants.

    """
    leaderboards = models.Leaderboard.objects.filter(id__in=leaderboard_ids)

    for leaderboard in leaderboards:

        participants = leaderboard.challenge.participants.all()
        # Add all participants to leaderboard as well.
        leaderboard.participants.add(*participants)

        for participant in participants:
            models.UserLeaderboard.objects.get_or_create(
                user=participant,
                leaderboard=leaderboard,
            )


# @periodic_task(run_every=crontab(day_of_week="Sunday", hour="20"))
def create_weekly_leaderboards():
    pass

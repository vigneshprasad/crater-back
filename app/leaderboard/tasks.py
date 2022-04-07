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
    leaderboards = private.get_active_leaderboards()

    for leaderboard in leaderboards:
        user_leaderboards = leaderboard.user_leaderboards.filter(is_active=True)
        for user_leaderboard in user_leaderboards:
            host = user_leaderboard.user
            minutes = conversations_models.Group.objects.filter(
                host=host,
                start__gte=leaderboard.start,
                end__lte=leaderboards.end
            ).aggregate(minutes=Sum("total_minutes"))["minutes"]

            user_leaderboards.total_minutes = minutes
            user_leaderboards.last_calculated_at = timezone.now()
            user_leaderboards.save()

        leaderboards.last_calculated_at = timezone.now()


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
def add_challenge_participants(leaderboard_ids):
    """Add challenge participants to leaderboard from challenge.

    Args:
        leaderboard_ids(list): List of leaderboard ids for which
            we have to add participants.

    """
    leaderboards = models.Leaderboard.objects.filter(id__in=leaderboard_ids)

    for leaderboard in leaderboards:
        participants = leaderboard.challenge.participants.all()

        for participant in participants:
            models.UserLeaderboard.objects.get_or_create(
                user=participant,
                leaderboard=leaderboard,
            )


# @periodic_task(run_every=crontab(day_of_week="Sunday", hour="20"))
def create_weekly_leaderboards():
    pass

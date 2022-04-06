import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.db.models import Sum
from django.utils import timezone

from conversations import models as conversations_models
from leaderboard import private
from leaderboard import models


@periodic_task(crontab(run_every="*/15"))
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

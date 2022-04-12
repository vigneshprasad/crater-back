from django.utils import timezone

from leaderboard import models


def get_active_leaderboards():

    now = timezone.now()
    leaderboards = models.Leaderboard.objects.filter(
        is_active=True,
        end__gte=now
    )
    return leaderboards


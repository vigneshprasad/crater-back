from django.utils import timezone

from leaderboard import models


def get_active_leaderboards():
    """Get all active leaderboards."""
    now = timezone.now()
    leaderboards = models.Leaderboard.objects.filter(
        is_active=True,
        end__gte=now
    )
    return leaderboards


def get_recently_ended_leaderboards(duration=1):
    """Returns leaderboards that ended some duration
    before today.

    Args:
        duration(int): Number of days the leaderboard has
            ended for.

    """
    now = timezone.now()
    yesterday = now - timezone.timedelta(days=duration)
    leaderboards = models.Leaderboard.objects.filter(
        end__lt=now,
        end__gte=yesterday
    )
    return leaderboards

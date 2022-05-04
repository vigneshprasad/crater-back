from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

from crater.auctions import models


@periodic_task(run_every=crontab(hour="0", minute="0"))
def close_ending_reward_auctions():
    """Close ending reward auctions."""
    end_date = timezone.now() + timezone.timedelta(days=1)
    reward_auctions = models.RewardAuction.objects.filter(
        is_closed=False,
        end__lte=end_date
    )
    # Mark all these reward auctions closed.
    reward_auctions.update(is_closed=True)


@periodic_task(run_every=crontab(hour="0", minute="0"))
def mark_reward_auction_active():
    pass

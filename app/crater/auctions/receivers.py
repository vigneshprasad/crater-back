from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auctions import models
from crater.auctions import signals


@receiver(post_save, model=models.Bid)
def send_bid_created(sender, instance, args, **kwargs):
    """Send bid placed signal if a bid is placed."""
    if not kwargs["created"]:
        return

    signals.bid_placed.send(
        sender=instance.__class__,
        instance=instance
    )

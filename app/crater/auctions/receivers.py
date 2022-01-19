from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auctions import models
from crater.auctions import signals
from crater.auctions import constants


@receiver(post_save, sender=models.Bid)
def send_bid_created(sender, instance, *args, **kwargs):
    """Send bid placed signal if a bid is placed."""
    if not kwargs["created"]:
        return

    signals.bid_placed.send(
        sender=instance.__class__,
        instance=instance
    )


@receiver(signals.bid_payment_charge_capture_setup)
def bid_payment_capturable_updated_success(sender, bid, *args, **kwargs):
    bid.status = constants.BID_STATUS_PENDING_ENUM
    bid.save()


@receiver(signals.bid_payment_charge_capture_success)
def bid_payment_charge_catured(sender, bid, *args, **kwargs):
    bid.status = constants.BID_STATUS_ACCEPTED_ENUM
    bid.save()


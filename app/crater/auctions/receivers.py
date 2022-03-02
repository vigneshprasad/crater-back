from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auctions import models
from crater.auctions import signals
from crater.auctions import constants
from crater.gateways.stripe_payments import signals as stripe_payment_signals


@receiver(post_save, sender=models.Bid)
def send_bid_created(sender, instance, *args, **kwargs):
    """Send bid placed signal if a bid is placed."""
    if not kwargs["created"]:
        return

    signals.bid_placed.send(
        sender=instance.__class__,
        instance=instance
    )


@receiver(post_save, sender=models.RewardAuction)
def send_auction_created_or_updated_signal(sender, instance, *args, **kwargs):
    now = timezone.now()
    if instance.end < now and not instance.is_active:
        return

    signals.auction_created_or_updated.send(
        sender=instance.__class__,
        auction=instance
    )


@receiver(signals.bid_payment_charge_capture_setup)
def bid_payment_capturable_updated_success(sender, bid, *args, **kwargs):
    bid.status = constants.BID_STATUS_PENDING_ENUM
    bid.save()


@receiver(signals.bid_payment_charge_capture_success)
def bid_payment_charge_catured(sender, bid, *args, **kwargs):
    bid.status = constants.BID_STATUS_ACCEPTED_ENUM
    bid.save()


@receiver(stripe_payment_signals.capture_payment_intent_success)
def update_auction_quantity_on_capture_success(sender, bid, *args, **kwargs):
    auction = bid.auction
    auction.quantity_sold += bid.quantity
    auction.save()

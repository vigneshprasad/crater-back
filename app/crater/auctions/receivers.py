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
    """Sends a signal on Reward auction creation."""

    now = timezone.now()
    # If the auction is in the past or is not active, don't send creation signal.
    if instance.end < now and not instance.is_active:
        return

    # TODO(Nishant): Need to change this to a separate create and update
    # auction signals.
    signals.auction_created_or_updated.send(
        sender=instance.__class__,
        auction=instance
    )


@receiver(signals.bid_payment_charge_capture_setup)
def bid_payment_charge_success(sender, bid, *args, **kwargs):
    """Updates bid status once Charge is created for a Bid."""
    bid.status = constants.BID_STATUS_PENDING_ENUM
    bid.save()


@receiver(signals.bid_payment_charge_capture_success)
def bid_payment_charge_captured(sender, bid, *args, **kwargs):
    """Updates the bid status once Charge is captured."""
    bid.mark_pending()


@receiver(stripe_payment_signals.capture_payment_intent_success)
def update_auction_quantity_on_capture_success(sender, bid, *args, **kwargs):
    """Update auction quantity on Payment Intent capture."""
    auction = bid.auction
    auction.update_quantity(bid.quantity)

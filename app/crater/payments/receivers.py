from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auctions import signals as auction_signals
from crater.gateways.stripe_payments import signals as stripe_signal
from crater.payments import models
from crater.payments import constants


@receiver(auction_signals.bid_placed)
def create_payment_on_bid_placed(sender, bid, *args, **kwargs):

    payment = models.Payment.objects.create(
        user=bid.bidder,
        amount=bid.amount
    )
    # Append the payment to the bid object.
    # bid.payment = payment
    # bid.save()

    return payment


@receiver(stripe_signal.capture_payment_intent_success)
def update_payment_status_on_charge_success(sender, bid, *args, **kwargs):
    """Update payment status to success once Charge creation is success."""
    payment = bid.payment
    if not payment:
        return

    payment.status = constants.PAYMENT_STATUS_SUCCESS_ENUM
    payment.save()

from django.db.models.signals import post_save
from django.dispatch import receiver

from crater.auctions import signals as auction_signals
from crater.payments import models


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

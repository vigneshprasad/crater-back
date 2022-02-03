from django.dispatch import receiver

from crater.auctions import signals as auction_signals
from crater.gateways.stripe_payments import tasks


@receiver(auction_signals.bid_accepted)
def capture_payment_intent_for_bid_accepted(sender, bid, *args, **kwargs):
    intent = bid.payment.stripe_payment_intent.first()
    if not intent:
        return

    tasks.capture_payment_intent_charge.delay(intent_id=intent.intent_id, bid_id=bid.id)

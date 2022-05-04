import logging

from django.dispatch import receiver

from crater.auctions import signals as auction_signals
from crater.gateways.stripe_payments import tasks


@receiver(auction_signals.bid_accepted)
def capture_payment_intent_for_bid_accepted(sender, bid, *args, **kwargs):
    """Starts capturing Payment intent on Stripe, once bid is accepted.

    Args:
        sender(Bid.__class__): Bid object class representation.
        bid(Bid): Bid that was accepted by the creator.

    """
    intent = bid.payment.stripe_payment_intent.first()
    # Throw an error if intent is not present.
    if not intent:
        logging.error("No intent found for Bid payment: {}".format(
            bid.id
        ))
        return False

    # Running the task in background, since we are calling Stipe API's.
    tasks.capture_payment_intent_charge.delay(intent_id=intent.intent_id, bid_id=bid.id)

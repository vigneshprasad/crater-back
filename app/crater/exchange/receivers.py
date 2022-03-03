from django.dispatch import receiver

from crater.auctions import signals
from crater.exchange import private
from crater.gateways.stripe_payments import signals as stripe_payment_signals


@receiver(stripe_payment_signals.capture_payment_intent_success)
def create_user_reward_for_payment_intent_capture(sender, bid, bidder, intent, *args, **kwargs):
    """Creates user reward on Bid payment capture.

    Args:
        sender(Bid.__class__): Class representation of Bid.
        bid(Bid): Bid object whose payment was captured.
        bidder(User): User who made the Bid.
        intent(PaymentIntent): Payment Intent that got captured.

    """
    private.update_or_create_user_reward(bid)


@receiver(signals.auction_created_or_updated)
def create_transaction_log_for_auction(sender, auction, *args, **kwargs):
    # private.update_or_create_transaction_log_for_auction(auction)
    pass

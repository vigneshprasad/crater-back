from django.dispatch import receiver

from crater.auctions import signals

from crater.gateways.stripe_payments import signals as stripe_payment_signals
from crater.exchange import private


@receiver(stripe_payment_signals.capture_payment_intent_success)
def create_transaction_log_for_capture_success(sender, bid, bidder, intent, *args, **kwargs):
    private.create_transaction_log_for_bid_payment_success(bid, bidder, intent)


@receiver(signals.auction_created_or_updated)
def create_transaction_log_for_auction(sender, auction, *args, **kwargs):
    private.update_or_create_transaction_log_for_auction(auction)
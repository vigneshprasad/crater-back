from django.dispatch import receiver

from crater.exchange import private
from crater.gateways.stripe_payments import signals as stripe_payment_signals
from crater.sales import signals as sale_signals


@receiver(stripe_payment_signals.capture_payment_intent_success)
def update_or_create_user_reward_for_payment_intent_capture(sender, bid, bidder, intent, *args, **kwargs):
    """Creates user reward on Bid payment capture.

    Args:
        sender(Bid.__class__): Class representation of Bid.
        bid(Bid): Bid object whose payment was captured.
        bidder(User): User who made the Bid.
        intent(PaymentIntent): Payment Intent that got captured.

    """
    private.update_or_create_user_reward(
        user=bid.bidder,
        reward=bid.auction.reward,
        quantity=bid.quantity
    )


@receiver(sale_signals.sale_payment_confirmed)
def update_or_create_user_reward_for_sale(sender, sale_log, *args, **kwargs):
    """Creates user reward on Bid payment capture.

        Args:
            sender(RewardSaleLog.__class__): Class representation of Sale log.
            sale_log(RewardSaleLog): Reward sale log that was confirmed..

        """
    private.update_or_create_user_reward(
        user=sale_log.user,
        reward=sale_log.reward_sale.reward,
        quantity=sale_log.quantity
    )


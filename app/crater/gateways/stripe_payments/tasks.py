import logging
from celery.task import task

from crater.auctions import models as auction_models

from crater.gateways.stripe_payments import models
from crater.gateways.stripe_payments.service import stripe_service
from crater.gateways.stripe_payments import signals


@task
def capture_payment_intent_charge(intent_id, bid_id):
    """Capture Payment charge on bid acceptance.

    Args:
        intent_id(int): Payment Intent ID for the payment
            associated with the Bid.
        bid_id(int): ID of the bid that has been accepted.

    """
    try:
        bid = auction_models.Bid.objects.get(id=bid_id)
    except auction_models.Bid.DoesNotExist:
        logging.error(
            "Bid missing from database during intent capture: {}".format(bid_id)
        )
        return False

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
    except models.PaymentIntent.DoesNotExist:
        logging.error(
            "Intent missing from database during intent capture: {}".format(intent_id)
        )
        return False

    # Capture intent from Stipe's side.
    intent = stripe_service.capture_payment_intent(intent=intent)

    # Send a signals on payment intent capture success.
    signals.capture_payment_intent_success.send(
        sender=intent.__class__,
        intent=intent,
        bidder=intent.payment.user,
        bid=bid,
    )

    return True


import logging
from celery.task import task

from crater.auctions import models as auction_models

from crater.gateways.stripe_payments import models
from crater.gateways.stripe_payments.service import stripe_service
from crater.gateways.stripe_payments import signals


def capture_payment_intent_charge(intent_id, bid_id):
    try:
        bid = auction_models.Bid.objects.get(id=bid_id)
        intent_obj = models.PaymentIntent.objects.get(intent_id=intent_id)
        intent = stripe_service.capture_payment_intent(intent=intent_obj)
        signals.capture_payment_intent_success.send(
            sender=intent.__class__,
            intent=intent,
            bidder=intent.payment.user,
            bid=bid,
        )

    except auction_models.Bid.DoesNotExist:
        logging.error(
            "Bid object missing from database during intent capture."
        )

    except models.PaymentIntent.DoesNotExist:
        logging.error(
            "Intent object missing from database during intent capture."
        )

from typing import List

from crater.gateways.stripe_payments import models
from crater.auctions import signals as auction_signals


def create_or_update_charges_list(data: List[dict]):

    for charge in data:
        create_or_update_charge_object(charge)


def create_or_update_charge_object(data: dict):
    """Create or update Stripe charge object.

    Args:
        data(dict): Charge object from Stripe.

    """
    charge_id = data["id"]
    amount = data["amount"] / 100
    amount_captured = data["amount_captured"] / 100
    amount_refunded = data["amount_refunded"] / 100
    captured = data["captured"]
    intent_id = data["payment_intent"]

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
    except models.PaymentIntent.DoesNotExist:
        return False

    payment_charge, _ = models.PaymentCharge.objects.update_or_create(
        charge_id=charge_id,
        payment_intent=intent,
        defaults={
            "amount": amount,
            "amount_captured": amount_captured,
            "amount_refunded": amount_refunded,
            "captured": captured,
            "data": data
        }
    )

    return True


def handle_charge_succeeded(data: dict):
    """Handler for Stripe charge.succeeded event

    Args:
        data(dict): Stripe Charge object dictionary

    """
    intent_id = data["payment_intent"]

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
    except models.PaymentIntent.DoesNotExist:
        return False

    bid = intent.payment.bid.all().first()
    if not bid:
        return False

    auction_signals.bid_payment_charge_capture_setup.send(
        sender=bid.__class__,
        bid=bid
    )


def handle_charge_captured(data: dict):
    """Handler for Stripe charge.captured webhook event

    Args:
        data(dict): Stripe Charge object dictionary

    """
    intent_id = data["payment_intent"]

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
    except models.PaymentIntent.DoesNotExist:
        return False

    bid = intent.payment.bid.all().first()
    if not bid:
        return False

    auction_signals.bid_payment_charge_capture_success.send(
        sender=bid.__class__,
        bid=bid
    )


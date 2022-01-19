from typing import List

from crater.gateways.stripe_payments import models
from crater.auctions import signals as auction_signals


def create_or_update_charges_list(data: List[dict]):
    for charge in data:
        create_or_update_charge_object(charge)


def create_or_update_charge_object(data: dict):
    charge_id = data["id"]
    amount = data["amount"] / 100
    amount_captured = data["amount_captured"] / 100
    amount_refunded = data["amount_refunded"] / 100
    captured = data["captured"]
    intent_id = data["payment_intent"]

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
        models.PaymentCharge.objects.update_or_create(
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

    except models.PaymentIntent.DoesNotExist:
        pass


def handle_charge_succeeded(data: dict):
    """Handler for Stripe charge.succeeded event

    Args:
        data: Stripe Charge object dictionary

    Returns:

    """
    intent_id = data["payment_intent"]

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
        bid = intent.payment.bid.all().first()
        if bid:
            auction_signals.bid_payment_charge_capture_setup.send(
                sender=bid.__class__,
                bid=bid
            )

    except models.PaymentIntent.DoesNotExist:
        pass


def handle_charge_captured(data: dict):
    """Handler for Stripe charge.captured webhook event

    Args:
        data: Stripe Charge object dictionary
    """
    intent_id = data["payment_intent"]

    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
        bid = intent.payment.bid.all().first()
        if bid:
            auction_signals.bid_payment_charge_capture_success.send(
                sender=bid.__class__,
                bid=bid
            )

    except models.PaymentIntent.DoesNotExist:
        pass

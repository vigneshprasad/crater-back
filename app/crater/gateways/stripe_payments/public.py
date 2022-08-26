import logging
from typing import List

from crater.gateways.stripe_payments import models
from crater.auctions import signals as auction_signals


def create_or_update_charges_list(charges: List[dict]):
    """Creat or update Stripe payment charges.

    Args:
        charges(list): List of payment charges.

    """
    for charge in charges:
        create_or_update_charge_object(charge)


def create_or_update_charge_object(charge: dict):
    """Create or update Stripe charge object.

    Args:
        charge(dict): Payment charge object from Stripe.

    """
    charge_id = charge["id"]
    # Amounts are returned in paisa from Stripe.
    amount = charge["amount"] / 100
    amount_captured = charge["amount_captured"] / 100
    amount_refunded = charge["amount_refunded"] / 100
    # Is the charge captured.
    captured = charge["captured"]
    # Payment intent for the charge.
    intent_id = charge["payment_intent"]

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
            "data": charge
        }
    )

    return True


def handle_charge_succeeded(charge: dict):
    """Handler for Stripe charge.succeeded event.

    Args:
        charge(dict): Stripe Charge object dictionary

    Note:
        Charge succeeded is only the setup of the
            charge or creation of charge on Stripe's
            side, doesn't mean the charge is successful.

    """
    intent_id = charge["payment_intent"]
    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
    except models.PaymentIntent.DoesNotExist:
        logging.error(
            "Charge succeeded without a Payment Intent: {}".format(charge["id"])
        )
        return False

    bid = intent.payment.bid.all().first()
    if not bid:
        logging.error(
            "No bid found for payment: {}".format(intent.payment.id)
        )
        return False

    auction_signals.bid_payment_charge_capture_setup.send(
        sender=bid.__class__,
        bid=bid
    )


def handle_charge_captured(charge: dict):
    """Handler for Stripe charge.captured webhook event

    Args:
        charge(dict): Stripe Charge object dictionary

    Note:
        Charge captured is fired when the amount is collected
            from the user. Meaning the payment has been
            successfully made.

    """
    intent_id = charge["payment_intent"]
    try:
        intent = models.PaymentIntent.objects.get(intent_id=intent_id)
    except models.PaymentIntent.DoesNotExist:
        logging.error(
            "Charge captured without a Payment Intent: {}".format(charge["id"])
        )
        return False

    bid = intent.payment.bid.all().first()
    if not bid:
        logging.error(
            "No bid found for payment: {}".format(intent.payment.id)
        )
        return False

    auction_signals.bid_payment_charge_capture_success.send(
        sender=bid.__class__,
        bid=bid
    )

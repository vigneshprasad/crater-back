from django.dispatch import receiver

from crater.gateways.stripe_payments import signals as stripe_signal
from crater.payments import constants


@receiver(stripe_signal.capture_payment_intent_success)
def update_payment_status_on_charge_success(sender, bid, *args, **kwargs):
    """Update payment status to success once Charge creation is success."""
    payment = bid.payment
    if not payment:
        return

    payment.status = constants.PAYMENT_STATUS_SUCCESS_ENUM
    payment.save()

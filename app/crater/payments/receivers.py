from django.dispatch import receiver

from crater.gateways.stripe_payments import signals as stripe_signal
from crater.payments import constants
from crater.sales import signals as sale_signals


@receiver(stripe_signal.capture_payment_intent_success)
def update_payment_status_on_charge_success(sender, bid, *args, **kwargs):
    """Update payment status to success once Charge creation is success."""
    payment = bid.payment
    if not payment:
        return

    payment.status = constants.PAYMENT_STATUS_SUCCESS_ENUM
    payment.save()


@receiver(sale_signals.sale_payment_confirmed)
def update_payment_for_sale_confirmation(sender, sale_log, *args, **kwargs):
    """Update the payment status if the sale is accepted by the creator.

    Args:
        sender(RewardSaleLog.__class__): Class representation of sale log.
        sale_log(RewardSaleLog): Reward sale log marked confirmed.

    """
    payment = sale_log.payment
    if not payment:
        return

    payment.status = constants.PAYMENT_STATUS_SUCCESS_ENUM
    payment.save()


@receiver(sale_signals.sale_payment_declined)
def update_payment_for_sale_rejection(sender, sale_log, *args, **kwargs):
    """Update the payment status if the sale is rejected by the creator.

    Args:
        sender(RewardSaleLog.__class__): Class representation of sale log.
        sale_log(RewardSaleLog): Reward sale log marked confirmed.

    """
    payment = sale_log.payment
    if not payment:
        return

    payment.status = constants.PAYMENT_STATUS_FAILED_ENUM
    payment.save()

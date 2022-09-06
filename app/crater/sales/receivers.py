import logging

from django.dispatch import receiver

from crater.sales import signals, tasks

LOGGER = logging.getLogger(__name__)


@receiver(signals.sale_payment_confirmed)
def update_reward_sale_quantity(sender, sale_log, *args, **kwargs):
    """Updates reward sale quantity once a sale log is moved to confirmed
        state.

    Args:
        sender(RewardSaleLog.__class__): Class representation of sale log.
        sale_log(RewardSaleLog): Reward sale log marked confirmed.

    """
    sale_log = sale_log
    reward_sale = sale_log.reward_sale
    if not reward_sale:
        LOGGER.error("No reward sale associated with Sale log: {}".format(sale_log.id))
        return

    # Update reward sale quantity.
    reward_sale.update_quantity(sale_log.quantity)


@receiver(signals.sale_payment_confirmed)
def send_notification_to_user_for_sale_confirmation(sender, sale_log, *args, **kwargs):
    """Sends notification to user is the sale is confirmed by
        the creator.

    Args:
        sender(RewardSaleLog.__class__): Class representation of sale log.
        sale_log(RewardSaleLog): Reward sale log marked confirmed.

    """
    tasks.send_notification_user_sale_accepted.delay(sale_log.id)


@receiver(signals.sale_payment_declined)
def send_notification_to_user_for_sale_rejection(sender, sale_log, *args, **kwargs):
    """Sends notification to user is the sale is declined by
        the creator.

    Args:
        sender(RewardSaleLog.__class__): Class representation of sale log.
        sale_log(RewardSaleLog): Reward sale log marked confirmed.

    """
    tasks.send_notification_user_sale_declined.delay(sale_log.id)


@receiver(signals.sale_created)
def send_notification_to_creator_for_sale_creation(sender, sale_log, *args, **kwargs):
    """Sends notification to creator when a user purchases a reward sale.

    Args:
        sender(RewardSaleLog.__class__): Class representation of sale log.
        sale_log(RewardSaleLog): Reward sale log marked confirmed.

    """
    tasks.send_notification_to_creator_for_sale.delay(sale_log.id)

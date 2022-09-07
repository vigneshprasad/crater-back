from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from crater.sales import constants as sale_constants, signals as sale_signals
from tokens import constants, models, private


@receiver(post_save, sender=models.TokenTransaction)
def create_token_log_for_token_transaction(sender, instance, *args, **kwargs):
    if not kwargs.get("created"):
        return

    transaction = instance
    # Calculate learn tokens by using crater tokens.
    user_token_log = models.UserTokenLog.objects.create(
        user=transaction.user,
        transaction=transaction,
        date=transaction.date
    )
    user_token_log.amount = transaction.amount
    user_token_log.type = constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    user_token_log.save()


@receiver(post_save, sender=models.UserTokenLog)
def update_or_create_user_token_for_user_token_log(sender, instance, *args, **kwargs):
    """Update/Create user token for a log creation."""
    if not kwargs.get("created"):
        return

    user_token_log = instance
    try:
        user_token = models.UserToken.objects.get(user=user_token_log.user)
    except models.UserToken.DoesNotExist:
        user_token = models.UserToken.objects.create(
            user=user_token_log,
            last_updated_at=timezone.now()
        )

    if user_token_log.type == constants.TRANSACTION_TYPE_ACQUIRED_ENUM:
        user_token.amount += user_token_log.amount
    elif user_token_log.type == constants.TRANSACTION_TYPE_REDEEMED_ENUM:
        user_token.amount -= user_token_log.amount

    user_token.save()


@receiver(sale_signals.sale_created)
def create_token_log_for_token_sale(sender, sale_log, *args, **kwargs):
    """Creates token log for a sale."""
    if not sale_log.type == sale_constants.SALE_PAYMENT_TYPE_LEARN_ENUM:
        return False

    # Redeem tokens for sale.
    token_log = private.redeem_tokens_for_user(sale_log.user, sale_log.amount)
    # Assign the token log to the sale.
    sale_log.token_log = token_log
    sale_log.save()
    # Mark confirmed once the tokens are redeemed.
    sale_log.mark_confirmed()

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from crater.sales import constants as sale_constants, signals as sale_signals
from tokens import models, private, public


@receiver(post_save, sender=models.TokenTransaction)
def update_or_create_token_log_for_token_transaction(sender, instance, *args, **kwargs):
    """Update or create token log for token transaction.

    Args:
        sender(TokenTransaction.__clas__): Class representation of Token transaction.
        instance(TokenTransaction): Token transaction that was updated/created.

    """
    transaction = instance
    # Calculate learn tokens by using crater tokens.
    models.UserTokenLog.objects.update_or_create(
        user=transaction.user,
        transaction=transaction,
        defaults={
            "date": transaction.date,
            "amount": transaction.amount
        }
    )


@receiver(post_save, sender=models.UserTokenLog)
def update_or_create_user_token_for_user_token_log(sender, instance, *args, **kwargs):
    """Update/Create user token for a log creation or update.

    Args:
        sender(UserTokenLog.__clas__): Class representation of user token log.
        instance(UserTokenLog): User token log that was updated/created.

    """

    user_token_log = instance
    user = user_token_log.user
    user_token, _ = models.UserToken.objects.get_or_create(user=user)
    user_token.amount = public.get_tokens_for_user(user)
    user_token.last_updated_at = timezone.now()
    user_token.save()


@receiver(sale_signals.sale_created)
def create_token_log_for_token_sale(sender, sale_log, *args, **kwargs):
    """Creates token log for a sale."""
    if not sale_log.payment_type == sale_constants.SALE_PAYMENT_TYPE_LEARN_ENUM:
        return False

    # Redeem tokens for sale.
    token_log = private.redeem_tokens_for_user(sale_log.user, sale_log.amount)
    # Assign the token log to the sale.
    sale_log.token_log = token_log
    sale_log.save()
    # Mark confirmed once the tokens are redeemed.
    sale_log.mark_sale_confirmed()

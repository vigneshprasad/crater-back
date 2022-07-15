from django.db.models.signals import post_save
from django.dispatch import receiver

from tokens import models, constants


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

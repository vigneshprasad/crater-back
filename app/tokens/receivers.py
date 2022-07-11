from django.db.models.signals import m2m_changed, post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.utils import timezone

from tokens import models


@receiver(post_save, sender=models.TokenTransaction)
def create_token_log_for_token_transaction(sender, instance, *args, **kwargs):
    if not kwargs.get("created"):
        return

    transaction = instance
    # Calculate learn tokens by using crater tokens.
    user_token_log = models.UserTokenLog.objects.create(
        user=transaction.user,
        transaction=transaction
    )
    user_token_log.tokens += transaction.amount
    user_token_log.type = models.UserTokenLog.TRANSACTION_TYPE[0][0]
    user_token_log.save()

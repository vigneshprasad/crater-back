from django.db.models import Sum

from tokens import models
from tokens import constants


def validate_token_redeem_for_user(user, amount):
    tokens_acquired = models.UserTokenLog.objects.filter(
        user=user,
        type=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    ).aggregate(
        total_amount=Sum("amount")
    )["total_amount"] or 0

    tokens_redeemed = models.UserTokenLog.objects.filter(
        user=user,
        type=constants.TRANSACTION_TYPE_REDEEMED_ENUM
    ).aggregate(
        total_amount=Sum("amount")
    )["total_amount"] or 0

    current_tokens = tokens_acquired - tokens_redeemed

    return current_tokens >= amount


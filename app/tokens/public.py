import datetime
import logging

from django.db.models import Sum

from tokens import constants, models

LOGGER = logging.getLogger(__name__)


def can_redeem_tokens(user, tokens):
    """Returns if the user can redeem provided tokens.

    Args:
        user(User): User who is redeeming the tokens.
        tokens(decimal/int): Tokens user wants to redeem.

    """
    user_tokens = get_tokens_for_user(user)
    if not user_tokens:
        return False

    return user_tokens >= tokens


def get_tokens_for_user(user):
    """Returns tokens user has for user i.e.
        acquired minus redeemed tokens

    Args:
        user(User): User we are getting the tokens for.

    """
    tokens_acquired = get_tokens_acquired_by_user(user)
    tokens_redeemed = get_tokens_redeemed_by_user(user)
    tokens = tokens_acquired - tokens_redeemed
    if tokens < 0:
        LOGGER.error("Tokens for user are negative: {}".format(user))
        return 0

    return tokens


def get_tokens_acquired_by_user(user):
    """Returns tokens acquired by the user.

    Args:
        user(User): User we are getting the aquired
         tokens for.

    """
    return models.UserTokenLog.objects.filter(
        user=user,
        type=constants.TRANSACTION_TYPE_ACQUIRED_ENUM
    ).aggregate(
        total_amount=Sum("amount")
    )["total_amount"] or 0


def get_tokens_redeemed_by_user(user):
    """Returns tokens redeemed by the user.

    Args:
        user(User): User we are getting the redeemed
            tokens for.

    """
    return models.UserTokenLog.objects.filter(
        user=user,
        type=constants.TRANSACTION_TYPE_REDEEMED_ENUM
    ).aggregate(
        total_amount=Sum("amount")
    )["total_amount"] or 0


def redeem_tokens_for_user(user, tokens):
    """Redeems tokens for a user.

    Args:
        user(User): User who is redeeming tokens.
        tokens(decimal/int): Number of tokens being
            redeemed.

    """
    if not can_redeem_tokens(user, tokens):
        return False

    # Create user token log for the redemption.
    models.UserTokenLog.objects.create(
        user=user,
        amount=tokens,
        type=constants.TRANSACTION_TYPE_REDEEMED_ENUM,
        date=datetime.date.today()
    )
    return True

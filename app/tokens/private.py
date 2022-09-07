import datetime

from tokens import models, constants


def redeem_tokens_for_user(user, tokens):
    """Redeems tokens for a user.

    Args:
        user(User): User who is redeeming tokens.
        tokens(decimal/int): Number of tokens being
            redeemed.

    """

    # Create user token log for the redemption.
    models.UserTokenLog.objects.create(
        user=user,
        amount=tokens,
        type=constants.TRANSACTION_TYPE_REDEEMED_ENUM,
        date=datetime.date.today()
    )
    return True

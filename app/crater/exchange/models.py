from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models
from crater.exchange import constants


class Transaction(base_models.BaseModel):

    TRANSACTION_TYPES = (
        (constants.TRANSACTION_TYPE_CRATER_TO_CREATOR_ENUM, constants.TRANSACTION_TYPE_CRATER_TO_CREATOR),
        (constants.TRANSACTION_TYPE_CREATOR_TO_USER_ENUM, constants.TRANSACTION_TYPE_CREATOR_TO_USER),
        (constants.TRANSACTION_TYPE_USER_TO_USER_ENUM, constants.TRANSACTION_TYPE_USER_TO_USER),
        (constants.TRANSACTION_TYPE_USER_TO_CREATOR_ENUM, constants.TRANSACTION_TYPE_USER_TO_CREATOR)
    )

    # Creator coin/token that is being bought or sold.
    coin = models.ForeignKey(
        "creator.Coin",
        on_delete=models.CASCADE
    )
    number_of_coins = models.IntegerField()

    # Buyer and seller of the coins.
    buyer = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="buy_transactions"
    )
    seller = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="sell_transactions"
    )

    # What price the coin was bought at. This denotes
    # total price of the coin price * quantity.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # What type of transaction is this, there are multiple transactions
    # that can happen in the system.

    # 1. Crater (market) introducing coins in the market for a creator.
    # 2. User buying/selling/bidding coins from a creator in exchange for rewards.
    # 3. User buying/selling/bidding coins among themselves.
    # 4. User selling coins back to creator/crater/market for rewards.

    type = models.PositiveIntegerField(choices=TRANSACTION_TYPES)


class UserCoinHolding(base_models.BaseModel):
    """This is a log for all users coin bought and redeemed.

    This is a single source of truth for the coins user is
    holding at any given point.

    """

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    coin = models.ForeignKey(
        "creator.Coin",
        on_delete=models.CASCADE
    )

    # Can be positive and negative based on whether
    # coin is being spent or bought.
    number_of_coins = models.IntegerField()

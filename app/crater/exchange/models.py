from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models
from crater.exchange import constants


class Transaction(base_models.BaseModel):

    TRANSACTION_TYPES = (
        (constants.TRANSACTION_TYPE_BID_ENUM, constants.TRANSACTION_TYPE_BID),
        (constants.TRANSACTION_TYPE_REDEMPTION_ENUM, constants.TRANSACTION_TYPE_REDEMPTION),
        (constants.TRANSACTION_TYPE_AUCTION_ENUM, constants.TRANSACTION_TYPE_AUCTION),
        (constants.TRANSACTION_TYPE_SALE_ENUM, constants.TRANSACTION_TYPE_SALE),
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

    payment = models.ForeignKey(
        "crater_payments.Payment",
        related_name="transactions",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # What type of transaction is this, there are multiple transactions
    # that can happen in the system.

    # 1. Bid: Refers Bid Transaction Log. (buyer: User, seller: Creator)
    # 2. Redemption: Refers to Reward Redemption Log/ (buyer: Creator, seller: User)
    # 3. Auction: Created when auction is created where coins are
    # assigned to creator. (buyer: Creator, seller: Crater)
    type = models.PositiveIntegerField(choices=TRANSACTION_TYPES)

    # Object ID of what is created in this Transaction. Based on the type.
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )


class UserReward(base_models.BaseModel):
    """This is a log for all user rewards bought and redeemed.

    Note:
        This is a single source of truth for the rewards a user is
            holding at any given point.

    """

    # TODO(Nishant): Change related names.
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="rewards"
    )
    reward = models.ForeignKey(
        "crater_rewards.Reward",
        on_delete=models.CASCADE,
        related_name="user_rewards"
    )

    # What is the total quantity of reward bought by the user.
    quantity = models.PositiveIntegerField(default=0)
    # What amount of rewards have to redeemed.
    redeemed_quantity = models.PositiveIntegerField(default=0)
    # Mark is redeemed when redeemed_quantity == quantity.
    is_redeemed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "reward")


class UserCoinHolding(base_models.BaseModel):
    """This is a log for all users coin bought and redeemed.

    Note:
        This is a single source of truth for coins user is
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

    class Meta:
        unique_together = ("user", "coin")

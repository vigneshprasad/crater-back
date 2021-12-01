from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

from base import models as base_models


class Transaction(base_models.BaseModel):

    TRANSACTION_TYPES = (
        ("market_creator", "Market to Creator"),
        ("creator_user", "Creator to User"),
        ("user_user", "User to User"),
        ("user_creator", "User to Creator")
    )

    coin = models.ForeignKey(
        "creator.Coin",
        on_delete=models.CASCADE
    )
    number_of_coins = models.IntegerField()

    # Buyer of the coin.
    buyer = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="buy_transactions"
    )
    # Seller of the coin.
    seller = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="sell_transactions"
    )

    # What price the coin was bought at.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # What type of transaction is this.
    type = models.CharField(
        choices=TRANSACTION_TYPES,
        max_length=64
    )


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

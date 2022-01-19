from django.contrib.auth import get_user_model
from django.db import models

from base import models as base_models
from crater.auctions import constants


class Auction(base_models.BaseModel):
    """Creator auctions for their Tokens."""

    coin = models.ForeignKey(
        "creator.Coin",
        related_name="auctions",
        on_delete=models.CASCADE
    )
    # Duration of the auction.
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_closed = models.BooleanField(default=False)

    # This key denotes if bids can be placed on the auction.
    is_active = models.BooleanField(default=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    number_of_coins = models.PositiveIntegerField()
    coins_sold = models.PositiveIntegerField(default=0)


class Bid(base_models.BaseModel):
    """Represents a bid placed on an auction or a bid from a user
        to another user for number of coins.

    """

    BID_STATUS_CHOICES = (
        (constants.BID_STATUS_PAYMENT_PENDING_ENUM, constants.BID_STATUS_PAYMENT_PENDING),
        (constants.BID_STATUS_PENDING_ENUM, constants.BID_STATUS_PENDING),
        (constants.BID_STATUS_ACCEPTED_ENUM, constants.BID_STATUS_ACCEPTED),
        (constants.BID_STATUS_REJECTED_ENUM, constants.BID_STATUS_REJECTED),
        (constants.BID_STATUS_CANCELLED_ENUM, constants.BID_STATUS_CANCELLED)
    )

    bidder = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )

    # What auction is the bid made for.
    auction = models.ForeignKey(
        Auction,
        null=True,
        blank=True,
        related_name="bids",
        on_delete=models.CASCADE
    )

    # Single coin price.
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_coins = models.PositiveIntegerField()

    # What is the status of the bid. Accepted status of bid
    # makes the exchange or coins.
    status = models.PositiveIntegerField(
        choices=BID_STATUS_CHOICES
    )

    # This key tells us if the bid has been processed completely.
    # Note: If this key is false, the bid is invalid.
    is_processed = models.BooleanField(default=False)

    # Attach a payment promise to the Bid.
    payment = models.ForeignKey(
        "crater_payments.Payment",
        related_name="bid",
        on_delete=models.CASCADE
    )

    @property
    def amount(self):
        return self.number_of_coins * self.bid_price


class CoinPriceLog(base_models.BaseModel):
    """This is the log of the price of a Creator token.

    Note:
        Ideally it'll always be the last accepted bid price.

    """

    coin = models.ForeignKey(
        "creator.Coin",
        related_name="log",
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
